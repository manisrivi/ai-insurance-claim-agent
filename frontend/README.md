# ClaimCare AI: frontend

Next.js (App Router) + TypeScript + Tailwind + shadcn/ui. No other UI or data libraries: the API is called with plain `fetch`.

## Run

```bash
cd frontend
npm install
cp .env.example .env.local   # points to the backend (default http://localhost:8000)
npm run dev                   # http://localhost:3000
```

The backend must be running (`uvicorn app.main:app --reload` in `backend/`).

## Pages

| Route | Page |
|---|---|
| `/` | Landing page |
| `/claims/new` | Submit a claim (form + bill PDF) |
| `/claims/[id]` | Claim status (refreshes every 3 s while processing) |
| `/track` | Search by Claim ID or policy number |
| `/officer/login` | Officer key login |
| `/officer` | Review list, details popup, approve / reject |

## Code map

- `src/lib/api.ts`: every backend call
- `src/lib/format.ts`: money and date formatting
- `src/lib/officer-key.ts`: officer key in `sessionStorage` (this tab only)
- `src/components/ui/`: shadcn components
- `src/components/`: header, status badges, officer details dialog
