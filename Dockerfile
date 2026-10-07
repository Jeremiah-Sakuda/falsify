# Python 3.12, pinned. The app targets 3.12 and CI pins it.
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FALSIFY_ENV=production \
    FALSIFY_DB=/data/falsify.db

WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY scripts/ ./scripts/
COPY LEDGER.md ./LEDGER.md

# Cloud Run's filesystem is instance-local and ephemeral. The demo state is
# disposable and reset by a job; production runs at max instances 1.
RUN mkdir -p /data && useradd -r -u 10001 falsify && chown -R falsify /data /app
USER falsify

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -fsS http://localhost:8080/healthz || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
