# Security settings and Claim ID format
import re

from app import db
from app.config import Settings


def test_claim_ids_are_random_and_readable():
    ids = {db.new_claim_id() for _ in range(500)}
    assert len(ids) == 500  # no repeats
    assert all(re.fullmatch(r"CLM-[A-HJ-NP-Z2-9]{4}-[A-HJ-NP-Z2-9]{4}", i) for i in ids)


def make(**kw):
    return Settings(database_url="postgresql://x:y@localhost/z", _env_file=None, **kw)


def test_production_refuses_short_officer_key():
    assert make(environment="production", officer_api_key="short-key").officer_key_ok is False
    assert make(environment="production", officer_api_key="x" * 32).officer_key_ok is True
    assert make(environment="development", officer_api_key="short-key").officer_key_ok is True
    assert make(officer_api_key="").officer_key_ok is False


def test_cors_origins_from_env():
    s = make(cors_origins="https://claimcare.app/, http://localhost:3000")
    assert s.cors_origin_list == ["https://claimcare.app", "http://localhost:3000"]
