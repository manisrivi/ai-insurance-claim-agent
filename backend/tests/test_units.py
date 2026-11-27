# Small unit tests for helpers
from app import db
from app.agent import runner
from app.rate_limit import RateLimiter


def test_update_claim_does_not_change_caller_dict(monkeypatch):
    class FakeConn:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def execute(self, *a): return None

    monkeypatch.setattr(db.pool, "connection", lambda: FakeConn())
    fields = {"status": "approved", "extracted_details": {"total_amount": 100}}
    db.update_claim("CLM-AAAA-BBBB", fields)
    assert fields == {"status": "approved", "extracted_details": {"total_amount": 100}}


def test_rate_limiter_window():
    limiter = RateLimiter(max_requests=2, window_seconds=60)
    assert [limiter.allow("ip"), limiter.allow("ip"), limiter.allow("ip")] == [True, True, False]
    assert limiter.allow("other-ip") is True


def test_resume_refuses_when_not_waiting(monkeypatch):
    monkeypatch.setattr(runner.db, "get_claim", lambda cid: {"claim_id": cid, "status": "approved"})
    try:
        runner.resume_claim("CLM-AAAA-BBBB", "rejected", None)
        assert False, "should raise"
    except runner.AlreadyDecidedError:
        pass


def _request(xff: str | None, peer: str = "10.0.0.5"):
    from starlette.requests import Request
    headers = [(b"x-forwarded-for", xff.encode())] if xff else []
    return Request({"type": "http", "client": (peer, 1234), "headers": headers})


def test_client_ip_ignores_fake_forwarded_header_by_default():
    from app.rate_limit import client_ip
    assert client_ip(_request("1.1.1.1"), hops=0) == "10.0.0.5"


def test_client_ip_behind_one_proxy_uses_the_ip_the_proxy_added():
    from app.rate_limit import client_ip
    # user faked "1.1.1.1"; the proxy appended the real IP at the end
    assert client_ip(_request("1.1.1.1, 203.0.113.9"), hops=1) == "203.0.113.9"
    assert client_ip(_request("2.2.2.2, 203.0.113.9"), hops=1) == "203.0.113.9"


def test_resume_refuses_when_another_officer_holds_the_lock(monkeypatch):
    from contextlib import contextmanager

    @contextmanager
    def busy(claim_id):
        yield False

    monkeypatch.setattr(runner.db, "get_claim", lambda cid: {"claim_id": cid, "status": "officer_review"})
    monkeypatch.setattr(runner.db, "decision_lock", busy)
    try:
        runner.resume_claim("CLM-AAAA-BBBB", "approved", None)
        assert False, "should raise"
    except runner.AlreadyDecidedError:
        pass
