# tools.py: tools the agent can use to look up real data
from langchain_core.tools import tool

from app import db

# This many claims (or more) in the period looks suspicious
SUSPICIOUS_CLAIM_COUNT = 3


@tool
def get_claim_history(patient_name: str, days: int = 30) -> dict:
    """Get how many claims a patient made in the last N days, including the current claim.
    Use it to check if a patient is claiming too often."""
    total = db.count_recent_claims(patient_name, days)
    return {
        "patient_name": patient_name,
        "days": days,
        "claims_in_period": total,
        "too_many_claims": total >= SUSPICIOUS_CLAIM_COUNT,
    }