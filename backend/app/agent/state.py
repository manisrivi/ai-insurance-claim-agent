# state.py: the "claim file" that travels through every agent desk (node)
from typing import Literal, TypedDict


class ClaimState(TypedDict, total=False):
    # total=False: boxes are filled step by step as the claim moves through the graph

    # --- From the form + PDF (filled at the start) ---
    claim_id: str
    patient_name: str
    policy_number: str
    hospital_name: str
    treatment: str
    admission_date: str
    discharge_date: str
    amount: float
    description: str | None
    bill_text: str

    # --- Document desk: what the bill really says ---
    bill_details: dict
    mismatches: list[str]

    # --- Policy desk: coverage check (RAG) ---
    is_covered: bool | None  # None = the policy text was not clear
    policy_limit: float | None
    policy_section: str
    policy_reason: str

    # --- Fraud desk: risk check ---
    risk: Literal["low", "high"]
    fraud_reasons: list[str]

    # --- Final result ---
    status: Literal["approved", "rejected", "officer_review"]
    reason: str
    officer_note: str | None