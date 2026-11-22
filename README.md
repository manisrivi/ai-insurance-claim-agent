# AI Insurance Claim Agent

An AI agent that reviews **health insurance claims**. A customer submits a claim form with a hospital bill PDF. A LangGraph agent reads the bill, checks the policy with RAG, checks for fraud, and then approves, rejects, or sends the claim to a human officer.

> Learning project. The policy and bills in `backend/data/` are fictional.

## How it works

```
Customer ──POST /claims (form + PDF)──▶ FastAPI ──save──▶ Supabase (status: processing)
                                           │
                                           └─ background task ─▶ LangGraph agent
                                                                  │
   START → document → policy (RAG) → fraud → decide ─┬─ approved / rejected ─▶ finalize → END
                                                     └─ officer_review ─▶ mark_for_officer → officer (pause ⏸)
                                                                                          │
                       Officer ──POST /officer/claims/{id}/decision──▶ resume ▶ finalize → END
```

| Node | Job |
|---|---|
| **document** | The LLM extracts bill fields (structured output). Code compares them with the form (amount, name, hospital, dates). |
| **policy** | RAG: ChromaDB finds the policy sections, then the LLM decides covered / not covered / unclear. Code checks that the cited section really exists in the retrieved text. |
| **fraud** | Always checks the claim history tool. The LLM gives a risk opinion; hard rules in code (mismatch, too many claims) force high risk. |
| **decide** | Pure code business rules: not covered → rejected; unclear, above the limit, high risk, or above ₹50,000 → officer review; otherwise approved. |
| **officer** | Human in the loop with `interrupt()`. The graph is saved in Postgres (`PostgresSaver`, `thread_id = claim_id`) and resumes after the officer decides. |
| **finalize** | Writes the final status to Supabase. |

**Production touches:** LLM fallback (Gemini → Claude), timeouts and retries, structured output, prompt-injection guards, business rules in code, a citation check, background processing, a safe fallback to the officer if the AI fails, PDF validation, parameterized SQL, an officer API key, LangSmith tracing, and tests with a fake LLM.

## Stack

Next.js · shadcn/ui · FastAPI · LangGraph · LangChain · Gemini (`gemini-3.5-flash-lite`, `gemini-embedding-001`) · Claude (backup) · ChromaDB · Supabase Postgres · psycopg 3 · pytest · LangSmith

## Run with Docker (easiest)

Needs Docker Desktop. Fill in `backend/.env` first (copy from `backend/.env.example`).

```bash
docker compose up --build     # first time (builds the images)
docker compose up             # next times
docker compose down           # stop
```

Open http://localhost:3000 (API docs: http://localhost:8000/docs).

## Run locally (without Docker)

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then fill in your real values
# Run sql/schema.sql once in the Supabase SQL editor
python -m app.rag.ingest      # load the policy into ChromaDB
uvicorn app.main:app --reload # open http://127.0.0.1:8000/docs
```

Frontend (Next.js + shadcn/ui), in a second terminal:

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev                   # open http://localhost:3000
```

Run the backend tests (no real DB or LLM needed):

```bash
pip install -r requirements-dev.txt
pytest -q
```

CI (GitHub Actions) runs the backend tests and the frontend lint + build on every push.

## API

| Method | Path | Who | Purpose |
|---|---|---|---|
| GET | `/health` | anyone | Server check |
| POST | `/claims` | customer | Submit the form + bill PDF → returns the Claim ID |
| GET | `/claims/{claim_id}` | customer | Status of one claim |
| GET | `/claims?policy_number=&patient_name=` | customer | Claims for a policy + patient (both must match) |
| GET | `/officer/claims` | officer (`X-Officer-Key`) | Claims waiting for review |
| POST | `/officer/claims/{claim_id}/decision` | officer (`X-Officer-Key`) | `{"decision": "approved" \| "rejected", "note": "..."}` |

## Before going live (checklist)

- [ ] `backend/.env`: `ENVIRONMENT=production` (hides API docs, refuses weak officer keys)
- [ ] `OFFICER_API_KEY`: 24+ random characters, kept secret
- [ ] `CORS_ORIGINS`: your live frontend URL, e.g. `https://claimcare.vercel.app`
- [ ] Frontend built with `NEXT_PUBLIC_API_URL` = your live backend URL
- [ ] ChromaDB: `CHROMA_MODE=cloud` + `CHROMA_API_KEY`, `CHROMA_TENANT`, `CHROMA_DATABASE` (Chroma Cloud), then `python -m app.rag.ingest` once
- [ ] Remove test data: `python -m app.reset_demo_data --yes` (deletes ALL claims)
- [ ] Note: Supabase free tier pauses after 7 days without use; Gemini free tier has rate limits

## Security notes

- Claim IDs are random (`CLM-7F3K-Q9XA`), so nobody can guess other people's claims
- Searching by policy needs the policy number **and** the patient name
- Rate limits per IP: submits, reads, officer requests (HTTP 429 when exceeded)
- ChromaDB runs locally (folder) in development and on Chroma Cloud in production (`CHROMA_MODE`); similarity is computed in code so both modes score the same
- PDFs are validated (type, size, pages, encryption) and never stored; only their text is kept
- Bill text and AI notes are never returned to customers
- Prompt-injection guard: bill text is treated as data; business rules are enforced in code

## Sample bills (`backend/data/sample_bills/`)

| Bill | Form amount | Expected |
|---|---|---|
| 1. Dengue, ₹18,500 | 18500 | approved |
| 2. Cosmetic rhinoplasty, ₹45,000 | 45000 | rejected (Section 3.1) |
| 3. Angioplasty, ₹75,000 | 75000 | officer_review (above ₹50,000) |
| 4. Viral fever, bill ₹6,500 | **80000** | officer_review (amount mismatch) |

## Next

- Officer login (replace the API key)
- Store PDFs in Supabase Storage + vision for scanned bills
- Docker, deploy, GitHub Actions
- Evals (golden dataset)
