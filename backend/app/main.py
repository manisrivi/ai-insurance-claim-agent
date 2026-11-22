# main.py: the API "reception desk"
import logging
import secrets
import threading
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, Header, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app import db
from app.agent import runner
from app.config import settings
from app.pdf_reader import MAX_FILE_SIZE_BYTES, PDFValidationError, read_pdf
from app.rate_limit import RateLimiter, limit
from app.schemas import ClaimCreated, ClaimForm, ClaimOut, ClaimStatus, OfficerClaimOut, OfficerDecision

logging.basicConfig(level=logging.INFO)

# Rate limits per IP (stop spam and protect the LLM bill)
submit_limiter = RateLimiter(settings.rate_limit_submit_per_min, 60)
read_limiter = RateLimiter(settings.rate_limit_read_per_min, 60)
officer_limiter = RateLimiter(settings.rate_limit_officer_per_min, 60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: connect to the database and prepare the agent
    db.open_pool()
    runner.start_agent()
    # Finish claims left "processing" by an earlier run (in the background, so startup stays fast)
    threading.Thread(target=runner.recover_stuck_claims, daemon=True).start()
    yield
    # Shutdown: close the connections
    runner.stop_agent()
    db.close_pool()


app = FastAPI(
    title="AI Insurance Claim Agent",
    version="0.3.0",
    lifespan=lifespan,
    # API docs only in development (in production they would show attackers every endpoint)
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None,
    openapi_url=None if settings.is_production else "/openapi.json",
)

# Only our own frontend site(s) may call this API from a browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Officer-Key"],
)


@app.get("/health")
def health():
    # Health check: is the server alive?
    return {"status": "ok"}


# ---------- Customer endpoints ----------

@app.post("/claims", response_model=ClaimCreated, status_code=201, dependencies=[Depends(limit(submit_limiter))])
def submit_claim(
    form: Annotated[ClaimForm, Form()],
    bill: Annotated[UploadFile, File(description="Hospital bill as a PDF")],
    background: BackgroundTasks,
):
    # 1. Read at most limit+1 bytes (a huge upload must not fill the server's memory)
    file_bytes = bill.file.read(MAX_FILE_SIZE_BYTES + 1)
    try:
        pdf = read_pdf(file_bytes, bill.filename or "", bill.content_type)
    except PDFValidationError as error:
        raise HTTPException(status_code=400, detail=str(error))

    # 2. Save the claim (with a random, unguessable Claim ID)
    row = db.create_claim({**form.model_dump(), "bill_text": pdf["text"]})

    # 3. Start the AI agent AFTER the response is sent (user does not wait)
    background.add_task(runner.run_claim, row["claim_id"])

    # 4. Reply instantly with the Claim ID
    return ClaimCreated(
        claim_id=row["claim_id"],
        status=row["status"],
        message="Claim submitted. Our AI is reviewing it now.",
    )


@app.get("/claims/{claim_id}", response_model=ClaimOut, dependencies=[Depends(limit(read_limiter))])
def get_claim(claim_id: str):
    # Search by Claim ID. The random ID works like a receipt number: only the owner knows it.
    claim = db.get_claim(claim_id.strip().upper())
    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found")
    return claim


@app.get("/claims", response_model=list[ClaimOut], dependencies=[Depends(limit(read_limiter))])
def search_claims(
    policy_number: Annotated[str, Query(min_length=3, max_length=50)],
    patient_name: Annotated[str, Query(min_length=2, max_length=100)],
):
    # Policy number AND patient name must both match (a policy number alone reveals nothing)
    return db.search_by_policy_and_patient(policy_number.strip(), " ".join(patient_name.split()))


# ---------- Officer endpoints ----------

def require_officer(x_officer_key: Annotated[str | None, Header()] = None):
    # Secret-key check. compare_digest = safe comparison (no timing tricks)
    if not settings.officer_key_ok:
        raise HTTPException(status_code=503, detail="Officer API is not configured")
    if not x_officer_key or not secrets.compare_digest(x_officer_key, settings.officer_api_key):
        raise HTTPException(status_code=401, detail="Invalid officer key")


officer_guard = [Depends(limit(officer_limiter)), Depends(require_officer)]


@app.get("/officer/claims", response_model=list[OfficerClaimOut], dependencies=officer_guard)
def officer_claims(status: Annotated[ClaimStatus, Query()] = "officer_review"):
    # Claims waiting for an officer (oldest first)
    return db.list_by_status(status)


@app.post("/officer/claims/{claim_id}/decision", response_model=ClaimOut, dependencies=officer_guard)
def officer_decision(claim_id: str, body: OfficerDecision):
    claim_id = claim_id.strip().upper()
    claim = db.get_claim(claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found")
    if claim["status"] != "officer_review":
        raise HTTPException(status_code=409, detail=f"Claim is '{claim['status']}', not waiting for an officer")

    # Resume the paused agent graph with the officer's answer
    logging.getLogger("audit").info("Officer decision: %s -> %s", claim_id, body.decision)
    try:
        runner.resume_claim(claim_id, body.decision, body.note)
    except runner.AlreadyDecidedError:
        raise HTTPException(status_code=409, detail="Claim was already decided")
    return db.get_claim(claim_id)
