# API tests: DB and agent are replaced with fakes
import pytest
from fastapi.testclient import TestClient

from app import main


@pytest.fixture(autouse=True)
def fresh_limits():
    # Each test starts with empty rate-limit counters
    for limiter in (main.submit_limiter, main.read_limiter, main.officer_limiter):
        limiter.reset()


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(main.db, "open_pool", lambda: None)
    monkeypatch.setattr(main.db, "close_pool", lambda: None)
    monkeypatch.setattr(main.runner, "start_agent", lambda: None)
    monkeypatch.setattr(main.runner, "stop_agent", lambda: None)
    monkeypatch.setattr(main.runner, "run_claim", lambda claim_id: None)
    monkeypatch.setattr(main.runner, "recover_stuck_claims", lambda: 0)
    with TestClient(main.app) as c:
        yield c


FORM = {
    "patient_name": "Ravi Kumar", "policy_number": "HLT-2026-0042",
    "hospital_name": "Sunrise Multispecialty Hospital", "treatment": "Dengue fever",
    "admission_date": "2026-11-10", "discharge_date": "2026-11-12", "amount": "18500",
}


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_submit_claim(client, monkeypatch, bill_bytes):
    monkeypatch.setattr(main.db, "create_claim", lambda data: {"claim_id": "CLM-2026-0009", "status": "processing"})
    res = client.post("/claims", data=FORM, files={"bill": ("bill.pdf", bill_bytes, "application/pdf")})
    assert res.status_code == 201
    assert res.json()["claim_id"] == "CLM-2026-0009"


def test_submit_rejects_bad_dates(client, bill_bytes):
    bad = {**FORM, "discharge_date": "2026-11-01"}
    res = client.post("/claims", data=bad, files={"bill": ("bill.pdf", bill_bytes, "application/pdf")})
    assert res.status_code == 422


def test_submit_rejects_non_pdf(client):
    res = client.post("/claims", data=FORM, files={"bill": ("bill.txt", b"hello", "text/plain")})
    assert res.status_code == 400


def test_unknown_claim_is_404(client, monkeypatch):
    monkeypatch.setattr(main.db, "get_claim", lambda claim_id: None)
    assert client.get("/claims/CLM-2026-9999").status_code == 404


def test_officer_needs_key(client):
    assert client.get("/officer/claims").status_code == 401
    assert client.get("/officer/claims", headers={"X-Officer-Key": "wrong"}).status_code == 401


def test_policy_search_needs_patient_name(client):
    assert client.get("/claims?policy_number=HLT-2026-0042").status_code == 422


def test_policy_search_with_name(client, monkeypatch):
    seen = {}
    monkeypatch.setattr(main.db, "search_by_policy_and_patient", lambda p, n: seen.update(p=p, n=n) or [])
    res = client.get("/claims", params={"policy_number": " HLT-2026-0042 ", "patient_name": " Ravi   Kumar "})
    assert res.status_code == 200
    assert seen == {"p": "HLT-2026-0042", "n": "Ravi Kumar"}


def test_submit_rate_limit(client, monkeypatch, bill_bytes):
    monkeypatch.setattr(main.db, "create_claim", lambda data: {"claim_id": "CLM-AAAA-BBBB", "status": "processing"})
    codes = [
        client.post("/claims", data=FORM, files={"bill": ("bill.pdf", bill_bytes, "application/pdf")}).status_code
        for _ in range(main.submit_limiter.max_requests + 1)
    ]
    assert codes[-1] == 429
    assert codes[:-1] == [201] * main.submit_limiter.max_requests


def test_officer_wrong_key_is_rate_limited(client):
    codes = [client.get("/officer/claims", headers={"X-Officer-Key": "x"}).status_code
             for _ in range(main.officer_limiter.max_requests + 1)]
    assert codes[-1] == 429


def test_officer_double_decision_returns_409(client, monkeypatch):
    monkeypatch.setattr(main.settings, "officer_api_key", "test-officer-key")
    monkeypatch.setattr(main.db, "get_claim", lambda cid: {"claim_id": cid, "status": "officer_review"})

    def already(*args):
        raise main.runner.AlreadyDecidedError("CLM-AAAA-BBBB")

    monkeypatch.setattr(main.runner, "resume_claim", already)
    res = client.post("/officer/claims/CLM-AAAA-BBBB/decision", json={"decision": "approved"},
                      headers={"X-Officer-Key": "test-officer-key"})
    assert res.status_code == 409


def test_officer_list_rejects_unknown_status(client):
    res = client.get("/officer/claims?status=hacked", headers={"X-Officer-Key": "test-officer-key"})
    assert res.status_code == 422


def test_oversized_upload_is_rejected_without_reading_it_all(client):
    big = b"%PDF" + b"0" * (6 * 1024 * 1024)
    res = client.post("/claims", data=FORM, files={"bill": ("big.pdf", big, "application/pdf")})
    assert res.status_code == 400
    assert "smaller than" in res.json()["detail"]
