# db.py: the "clerk" that reads and writes the claims table in Supabase
import secrets

from psycopg import errors, sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from psycopg_pool import ConnectionPool

from app.config import settings

# Connection pool: up to 5 ready connections, reused for every request
pool = ConnectionPool(
    settings.database_url,
    min_size=1,
    max_size=5,
    kwargs={"row_factory": dict_row, "autocommit": True},
    open=False,
)

# Only these columns may change after a claim is submitted
UPDATABLE_COLUMNS = {
    "bill_text",
    "extracted_details",
    "status",
    "risk",
    "reason",
    "officer_note",
}


def open_pool():
    # Connect when the app starts (fails fast if DATABASE_URL is wrong)
    pool.open(wait=True)


def close_pool():
    # Close connections when the app stops
    pool.close()


# Claim ID letters: no 0/O or 1/I/L, so people can read and type them easily
CLAIM_ID_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"


def new_claim_id() -> str:
    # Random, unguessable ID like CLM-7F3K-Q9XA (31^8 = about 850 billion options)
    chars = "".join(secrets.choice(CLAIM_ID_ALPHABET) for _ in range(8))
    return f"CLM-{chars[:4]}-{chars[4:]}"


def create_claim(data: dict) -> dict:
    # Insert a new claim with a random Claim ID (retry in the very rare case of a clash)
    query = """
        insert into claims (
            claim_id, patient_name, policy_number, hospital_name, treatment,
            admission_date, discharge_date, amount, description, bill_text
        )
        values (
            %(claim_id)s, %(patient_name)s, %(policy_number)s, %(hospital_name)s, %(treatment)s,
            %(admission_date)s, %(discharge_date)s, %(amount)s, %(description)s, %(bill_text)s
        )
        returning claim_id, status, created_at
    """
    for _ in range(5):
        try:
            with pool.connection() as conn:
                return conn.execute(query, {**data, "claim_id": new_claim_id()}).fetchone()
        except errors.UniqueViolation:
            continue
    raise RuntimeError("Could not create a unique claim ID")


def get_claim(claim_id: str) -> dict | None:
    # Find one claim by its Claim ID (None if not found)
    with pool.connection() as conn:
        return conn.execute(
            "select * from claims where claim_id = %s", (claim_id,)
        ).fetchone()


def search_by_policy_and_patient(policy_number: str, patient_name: str) -> list[dict]:
    # Both must match (case-insensitive), so a policy number alone reveals nothing
    with pool.connection() as conn:
        return conn.execute(
            """
            select * from claims
            where upper(policy_number) = upper(%s)
              and lower(patient_name) = lower(%s)
            order by created_at desc
            """,
            (policy_number, patient_name),
        ).fetchall()


def update_claim(claim_id: str, fields: dict) -> None:
    # Update allowed fields only (e.g. status, risk, reason)
    fields = dict(fields)  # copy: never change the caller's dict
    bad = set(fields) - UPDATABLE_COLUMNS
    if bad:
        raise ValueError(f"Cannot update columns: {bad}")
    if "extracted_details" in fields:
        fields["extracted_details"] = Jsonb(fields["extracted_details"])

    set_parts = [
        sql.SQL("{} = {}").format(sql.Identifier(name), sql.Placeholder(name))
        for name in fields
    ]
    query = sql.SQL("update claims set {}, updated_at = now() where claim_id = {}").format(
        sql.SQL(", ").join(set_parts), sql.Placeholder("claim_id")
    )
    with pool.connection() as conn:
        conn.execute(query, {**fields, "claim_id": claim_id})


def count_recent_claims(patient_name: str, days: int = 30) -> int:
    # How many claims this patient made in the last N days (fraud signal)
    with pool.connection() as conn:
        row = conn.execute(
            """
            select count(*) as total from claims
            where lower(patient_name) = lower(%s)
              and created_at > now() - make_interval(days => %s)
            """,
            (patient_name, days),
        ).fetchone()
        return row["total"]

def list_by_status(status: str, limit: int = 100) -> list[dict]:
    # Officer list: claims with one status, oldest first (first come, first served)
    with pool.connection() as conn:
        return conn.execute(
            "select * from claims where status = %s order by created_at asc limit %s",
            (status, limit),
        ).fetchall()
