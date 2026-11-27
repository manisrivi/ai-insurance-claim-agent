# Business rules: pure code, so we can test every case without an LLM
from app.agent import nodes
from app.agent.nodes import BillDetails, FraudCheck, PolicyCheck, _find_mismatches, decide_node


def test_no_mismatch_when_bill_matches(base_state):
    bill = BillDetails(patient_name="Ravi Kumar", total_amount=18500, admission_date="2026-11-10")
    assert _find_mismatches(base_state, bill) == []


def test_names_ignore_spaces_and_case(base_state):
    bill = BillDetails(hospital_name="Mayo Clinic")
    assert _find_mismatches({**base_state, "hospital_name": "Mayoclinic"}, bill) == []


def test_amount_mismatch(base_state):
    bill = BillDetails(total_amount=6500)
    problems = _find_mismatches({**base_state, "amount": 80000}, bill)
    assert problems == ["Amount mismatch: form says Rs 80,000, bill says Rs 6,500"]


def test_small_rounding_is_ok(base_state):
    bill = BillDetails(total_amount=18500.5)
    assert _find_mismatches(base_state, bill) == []


def test_not_covered_is_rejected(base_state):
    state = {**base_state, "is_covered": False, "policy_section": "Section 3.1", "policy_reason": "Cosmetic", "risk": "low"}
    assert decide_node(state)["status"] == "rejected"


def test_clean_small_claim_is_approved(base_state):
    state = {**base_state, "is_covered": True, "policy_limit": 100000, "policy_section": "Section 2.1",
             "policy_reason": "Dengue is covered", "risk": "low", "fraud_reasons": []}
    assert decide_node(state)["status"] == "approved"


def test_big_amount_goes_to_officer(base_state):
    state = {**base_state, "amount": 75000, "is_covered": True, "policy_limit": 300000, "risk": "low"}
    result = decide_node(state)
    assert result["status"] == "officer_review"
    assert "50,000" in result["reason"]


def test_high_risk_goes_to_officer(base_state):
    state = {**base_state, "is_covered": True, "risk": "high", "fraud_reasons": ["Amount mismatch"]}
    assert decide_node(state)["status"] == "officer_review"


def test_unclear_coverage_goes_to_officer(base_state):
    state = {**base_state, "is_covered": None, "policy_reason": "No rule", "risk": "low"}
    assert decide_node(state)["status"] == "officer_review"


def test_above_policy_limit_goes_to_officer(base_state):
    state = {**base_state, "amount": 40000, "is_covered": True, "policy_limit": 30000, "risk": "low"}
    assert decide_node(state)["status"] == "officer_review"


def test_code_overrides_llm_low_risk(base_state, monkeypatch):
    # LLM says "low", but a mismatch exists, so code forces "high"
    from tests.conftest import FakeLLM
    monkeypatch.setattr(nodes, "get_structured_llm", FakeLLM({"FraudCheck": FraudCheck(risk="low", reasons=["Looks normal"])}))
    monkeypatch.setattr(nodes.get_claim_history, "func", lambda patient_name, days=30: {
        "patient_name": patient_name, "days": days, "claims_in_period": 1, "too_many_claims": False})
    result = nodes.fraud_node({**base_state, "mismatches": ["Amount mismatch"]})
    assert result == {"risk": "high", "fraud_reasons": ["Amount mismatch"]}


def test_policy_citation_must_exist(base_state, monkeypatch):
    # The AI cites a section that is NOT in the retrieved text -> treat as unclear
    from tests.conftest import FakeLLM
    monkeypatch.setattr(nodes, "search_policy", lambda q: [{"text": "Section 2.1 Dengue covered", "page": 1}])
    monkeypatch.setattr(nodes, "get_structured_llm", FakeLLM({"PolicyCheck": PolicyCheck(
        coverage="covered", per_claim_limit=100000, section="Section 9.9", reason="made up")}))
    assert nodes.policy_node(base_state)["is_covered"] is None


def test_fraud_reasons_not_repeated(base_state, monkeypatch):
    from tests.conftest import FakeLLM
    monkeypatch.setattr(nodes, "get_structured_llm", FakeLLM({"FraudCheck": FraudCheck(
        risk="high", reasons=["The patient made too many claims recently", "Skin clinic doing heart surgery"])}))
    monkeypatch.setattr(nodes.get_claim_history, "func", lambda patient_name, days=30: {
        "patient_name": patient_name, "days": days, "claims_in_period": 3, "too_many_claims": True})
    result = nodes.fraud_node({**base_state, "mismatches": []})
    assert result["fraud_reasons"] == ["3 claims in the last 30 days", "Skin clinic doing heart surgery"]


def test_citation_must_match_exact_section(base_state, monkeypatch):
    # AI cites "Section 2.1" but only "Section 2.10" exists -> not a valid citation
    from tests.conftest import FakeLLM
    monkeypatch.setattr(nodes, "search_policy", lambda q: [{"text": "Section 2.10 Something covered", "page": 1}])
    monkeypatch.setattr(nodes, "get_structured_llm", FakeLLM({"PolicyCheck": PolicyCheck(
        coverage="covered", per_claim_limit=None, section="Section 2.1", reason="x")}))
    assert nodes.policy_node(base_state)["is_covered"] is None


def test_citation_at_end_of_sentence_is_valid(base_state, monkeypatch):
    from tests.conftest import FakeLLM
    monkeypatch.setattr(nodes, "search_policy", lambda q: [{"text": "Dengue is covered, see Section 2.1.", "page": 1}])
    monkeypatch.setattr(nodes, "get_structured_llm", FakeLLM({"PolicyCheck": PolicyCheck(
        coverage="covered", per_claim_limit=100000, section="Section 2.1", reason="ok")}))
    assert nodes.policy_node(base_state)["is_covered"] is True


def test_name_match_is_whole_words():
    from app.agent.nodes import _same_text
    assert _same_text("Ravi", "Ravi Kumar")            # part of the full name
    assert _same_text("Mayoclinic", "Mayo Clinic")     # spaces ignored
    assert _same_text("RAVI KUMAR", "ravi kumar.")      # case and punctuation ignored
    assert not _same_text("An", "Jane Doe")             # short text hidden inside another name
    assert not _same_text("John Doe", "Jane Doe")
