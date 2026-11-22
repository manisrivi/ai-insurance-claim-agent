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
