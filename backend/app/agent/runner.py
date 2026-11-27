# runner.py: starts the agent for a claim, and resumes it after an officer decides
import logging

from langgraph.types import Command

from app import db
from app.agent.graph import build_graph, close_checkpointer, open_checkpointer

logger = logging.getLogger(__name__)

_graph = None


class AlreadyDecidedError(Exception):
    pass


def start_agent() -> None:
    # Called once when the API starts
    global _graph
    _graph = build_graph(checkpointer=open_checkpointer())


def stop_agent() -> None:
    close_checkpointer()


def _config(claim_id: str) -> dict:
    # thread_id = claim_id: each claim has its own saved progress
    return {"configurable": {"thread_id": claim_id}, "run_name": f"claim-{claim_id}"}


def _state_from_row(row: dict) -> dict:
    # DB gives date objects and Decimal; the agent wants simple text and numbers
    return {
        "claim_id": row["claim_id"],
        "patient_name": row["patient_name"],
        "policy_number": row["policy_number"],
        "hospital_name": row["hospital_name"],
        "treatment": row["treatment"],
        "admission_date": str(row["admission_date"]),
        "discharge_date": str(row["discharge_date"]),
        "amount": float(row["amount"]),
        "description": row["description"],
        "bill_text": row["bill_text"] or "",
    }


def run_claim(claim_id: str) -> None:
    # Runs in the background after submit. Never crashes the API.
    try:
        row = db.get_claim(claim_id)
        if row is None:
            logger.error("Claim %s not found", claim_id)
            return
        _graph.invoke(_state_from_row(row), _config(claim_id))
    except Exception:
        logger.exception("Agent failed for claim %s", claim_id)
        # Safe fallback: a human checks it
        try:
            db.update_claim(claim_id, {
                "status": "officer_review",
                "reason": "Automatic review failed. An officer will check this claim.",
            })
        except Exception:
            # DB is down too: the claim stays "processing" and is retried at the next start
            logger.exception("Could not save the fallback status for claim %s", claim_id)


def recover_stuck_claims() -> int:
    # Called at startup. Background tasks die when the server stops, so any claim
    # still "processing" now was never finished. Run the agent for each one again.
    stuck = db.list_by_status("processing")
    for row in stuck:
        logger.info("Recovering stuck claim %s", row["claim_id"])
        run_claim(row["claim_id"])
    return len(stuck)


def is_waiting_for_officer(claim_id: str) -> bool:
    # True if the graph is paused at the officer desk
    snapshot = _graph.get_state(_config(claim_id))
    return bool(snapshot.next) and "officer" in snapshot.next


def resume_claim(claim_id: str, decision: str, note: str | None) -> None:
    # Officer decided: continue the paused graph, or update directly if the AI had failed
    row = db.get_claim(claim_id)
    if row is None or row["status"] != "officer_review":
        raise AlreadyDecidedError(claim_id)
    # Two officers clicking at the same moment: only one gets the lock and decides
    with db.decision_lock(claim_id) as got_lock:
        if not got_lock:
            raise AlreadyDecidedError(claim_id)
        row = db.get_claim(claim_id)  # check again inside the lock
        if row is None or row["status"] != "officer_review":
            raise AlreadyDecidedError(claim_id)
        _apply_decision(claim_id, decision, note)


def _apply_decision(claim_id: str, decision: str, note: str | None) -> None:
    if is_waiting_for_officer(claim_id):
        _graph.invoke(Command(resume={"decision": decision, "note": note}), _config(claim_id))
    else:
        db.update_claim(claim_id, {
            "status": decision,
            "officer_note": note,
            "reason": f"Officer {decision}.",
        })
