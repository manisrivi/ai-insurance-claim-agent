# conftest.py: shared test setup. Tests never call the real DB or real LLM.
import os
from pathlib import Path

# Fake settings BEFORE the app is imported (env vars win over .env)
os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5432/test"
os.environ["GOOGLE_API_KEY"] = "test-key"
os.environ["OFFICER_API_KEY"] = "test-officer-key"
os.environ["LANGSMITH_TRACING"] = "false"

import pytest

BILLS = Path(__file__).resolve().parents[1] / "data" / "sample_bills"


@pytest.fixture
def bill_bytes():
    return (BILLS / "bill_1_small_valid.pdf").read_bytes()


class FakeLLM:
    # Pretends to be get_structured_llm(schema): returns a ready answer per schema
    def __init__(self, answers: dict):
        self.answers = answers

    def __call__(self, schema):
        answer = self.answers[schema.__name__]
        return type("Fake", (), {"invoke": lambda _self, _messages: answer})()


@pytest.fixture
def base_state():
    return {
        "claim_id": "CLM-2026-0001",
        "patient_name": "Ravi Kumar",
        "policy_number": "HLT-2026-0042",
        "hospital_name": "Sunrise Multispecialty Hospital",
        "treatment": "Dengue fever",
        "admission_date": "2026-11-10",
        "discharge_date": "2026-11-12",
        "amount": 18500.0,
        "description": None,
        "bill_text": "Sunrise Multispecialty Hospital bill for Ravi Kumar, dengue, total 18500",
    }
