# Full graph run with a fake LLM, fake DB and in-memory checkpointer
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from app.agent import nodes
from app.agent.graph import build_graph
from app.agent.nodes import BillDetails, FraudCheck, PolicyCheck
from tests.conftest import FakeLLM


def _setup(monkeypatch, bill_total, coverage="covered", section="Section 2.1"):
    saved = {}
    monkeypatch.setattr(nodes.db, "update_claim", lambda cid, fields: saved.update(fields))
    monkeypatch.setattr(nodes.get_claim_history, "func", lambda patient_name, days=30: {
        "patient_name": patient_name, "days": days, "claims_in_period": 1, "too_many_claims": False})
    monkeypatch.setattr(nodes, "search_policy", lambda q: [
        {"text": "Section 2.1 Dengue covered. Section 3.1 Cosmetic NOT covered.", "page": 1}])
    monkeypatch.setattr(nodes, "get_structured_llm", FakeLLM({
        "BillDetails": BillDetails(patient_name="Ravi Kumar", total_amount=bill_total),
        "PolicyCheck": PolicyCheck(coverage=coverage, per_claim_limit=100000, section=section, reason="Policy rule"),
        "FraudCheck": FraudCheck(risk="low", reasons=["Normal stay"]),
    }))
    return saved


def test_clean_claim_is_approved(monkeypatch, base_state):
    saved = _setup(monkeypatch, bill_total=18500)
    graph = build_graph(InMemorySaver())
    graph.invoke(base_state, {"configurable": {"thread_id": "t1"}})
    assert saved["status"] == "approved"


def test_cosmetic_claim_is_rejected(monkeypatch, base_state):
    saved = _setup(monkeypatch, bill_total=18500, coverage="not_covered", section="Section 3.1")
    graph = build_graph(InMemorySaver())
    graph.invoke(base_state, {"configurable": {"thread_id": "t2"}})
    assert saved["status"] == "rejected"


def test_mismatch_pauses_then_officer_approves(monkeypatch, base_state):
    saved = _setup(monkeypatch, bill_total=6500)
    graph = build_graph(InMemorySaver())
    config = {"configurable": {"thread_id": "t3"}}

    graph.invoke({**base_state, "amount": 80000}, config)
    assert saved["status"] == "officer_review"
    assert graph.get_state(config).next == ("officer",)

    graph.invoke(Command(resume={"decision": "approved", "note": "Checked with hospital"}), config)
    assert saved["status"] == "approved"
    assert saved["officer_note"] == "Checked with hospital"


def test_recover_reruns_processing_claims(monkeypatch):
    from app.agent import runner
    ran = []
    monkeypatch.setattr(runner.db, "list_by_status", lambda status: [{"claim_id": "CLM-1"}, {"claim_id": "CLM-2"}])
    monkeypatch.setattr(runner, "run_claim", lambda claim_id: ran.append(claim_id))
    assert runner.recover_stuck_claims() == 2
    assert ran == ["CLM-1", "CLM-2"]
