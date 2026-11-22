# Backend image: FastAPI + LangGraph agent
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# 1. Install packages first (this layer is cached until requirements.txt changes)
COPY requirements.txt .
RUN pip install -r requirements.txt

# 2. Copy the app code and the policy PDF (secrets come from env vars, never baked in)
COPY app ./app
COPY data ./data
COPY docker-entrypoint.sh .

# 3. Run as a normal user, not root (safer)
RUN useradd --create-home appuser && mkdir -p chroma_db && chown -R appuser /app
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=40s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

ENTRYPOINT ["sh", "docker-entrypoint.sh"]
