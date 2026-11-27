#!/bin/sh
# Container start: make sure the policy is in ChromaDB (local or cloud), then start the API
set -e
python -m app.rag.ingest --if-empty
# The real user IP behind a proxy is read safely in app/rate_limit.py (TRUSTED_PROXY_HOPS),
# so uvicorn must NOT trust X-Forwarded-For from everyone (users could fake their IP).
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --no-proxy-headers
