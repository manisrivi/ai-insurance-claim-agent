# schemas.py: the "checklist" for data coming IN and going OUT of the API
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

# The only allowed claim statuses (same as the database check)
ClaimStatus = Literal["processing", "approved", "rejected", "officer_review"]


class ClaimForm(BaseModel):
    # IN: the claim form fields (the PDF comes separately as a file)
    model_config = ConfigDict(str_strip_whitespace=True)

    patient_name: str = Field(min_length=2, max_length=100)
    policy_number: str = Field(min_length=3, max_length=50)
    hospital_name: str = Field(min_length=2, max_length=150)
    treatment: str = Field(min_length=2, max_length=150)
    admission_date: date
    discharge_date: date
    amount: float = Field(gt=0, le=10_000_000)
    description: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def check_dates(self):
        # Rules that compare two fields together
        if self.discharge_date < self.admission_date:
            raise ValueError("Discharge date cannot be before admission date")
        if self.admission_date > date.today():
            raise ValueError("Admission date cannot be in the future")
        return self


class ClaimCreated(BaseModel):
    # OUT: response right after submitting
    claim_id: str
    status: ClaimStatus
    message: str


CUSTOMER_MESSAGES = {
    "processing": "Our AI is reading your bill and checking your policy.",
    "officer_review": "Your claim needs a manual check by a claims officer. The decision will appear here.",
}


def customer_message(status: str, reason: str | None) -> str:
    # What a customer may see. Fraud checks and AI notes stay internal: showing them
    # would teach a fraudster exactly what to change next time.
    if status in CUSTOMER_MESSAGES:
        return CUSTOMER_MESSAGES[status]
    reason = reason or ""
    if reason.startswith("Officer "):
        return f"{'Approved' if status == 'approved' else 'Rejected'} after review by a claims officer."
    # AI decisions only quote the policy ("Covered under Section 2.1 ..." / "Not covered (Section 3.1) ...")
    if reason.startswith(("Covered under", "Not covered")):
        return reason
    return "Your claim was approved." if status == "approved" else "Your claim was rejected."


class ClaimOut(BaseModel):
    # OUT: what the customer sees. No risk level and no AI notes (internal only).
    claim_id: str
    patient_name: str
    policy_number: str
    hospital_name: str
    treatment: str
    admission_date: date
    discharge_date: date
    amount: float
    description: str | None = None
    status: ClaimStatus
    message: str = ""
    officer_note: str | None = None
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="before")
    @classmethod
    def add_customer_message(cls, data):
        # Build the safe message from the database row (status + internal reason)
        if isinstance(data, dict) and "status" in data:
            data = {**data, "message": customer_message(data["status"], data.get("reason"))}
        return data


class OfficerDecision(BaseModel):
    # IN: an officer's final decision on a claim
    model_config = ConfigDict(str_strip_whitespace=True)

    decision: Literal["approved", "rejected"]
    note: str | None = Field(default=None, max_length=1000)


class OfficerClaimOut(ClaimOut):
    # OUT: officers also see the risk, the AI notes and what the AI read from the bill
    risk: Literal["low", "high"] | None = None
    reason: str | None = None
    extracted_details: dict | None = None

