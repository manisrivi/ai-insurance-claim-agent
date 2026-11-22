#!/bin/sh
# Container start: make sure the policy is in ChromaDB (local or cloud), then start the API
set -e
python -m app.rag.ingest --if-empty
# --proxy-headers: behind a load balancer, use the real user IP (for rate limits)
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips="*"
