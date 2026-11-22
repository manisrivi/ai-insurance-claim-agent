#!/usr/bin/env bash
# start.sh: starts the backend (port 8000) and the frontend (port 3000) together.
# Run from the project folder:  bash start.sh      Stop both: Ctrl + C
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "🐍 Backend setup..."
cd "$ROOT/backend"
if [ ! -f .env ]; then
  echo "❌ backend/.env is missing. Copy .env.example to .env and fill it in."; exit 1
fi
if ! grep -q "^OFFICER_API_KEY=." .env; then
  echo "⚠️  OFFICER_API_KEY is not in backend/.env. Officer login will not work until you add it."
fi
[ -d venv ] || python3 -m venv venv
./venv/bin/pip install -q -r requirements.txt
echo "📘 Checking the policy in ChromaDB..."
./venv/bin/python -m app.rag.ingest --if-empty

echo "⚛️  Frontend setup..."
cd "$ROOT/frontend"
[ -f .env.local ] || cp .env.example .env.local
[ -d node_modules ] || npm install

# Start both; Ctrl + C stops both
cd "$ROOT/backend"
./venv/bin/uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!
cd "$ROOT/frontend"
npm run dev &
FRONTEND_PID=$!
trap 'echo; echo "Stopping..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0' INT TERM

sleep 6
echo ""
echo "✅ Running!  Open http://localhost:3000   (API docs: http://localhost:8000/docs)"
echo "   Press Ctrl + C to stop both."
wait
