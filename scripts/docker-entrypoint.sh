#!/usr/bin/env sh
set -eu

echo "[entrypoint] Running Alembic migrations..."
alembic upgrade head

echo "[entrypoint] Starting API with Gunicorn + Uvicorn worker..."
exec gunicorn app.main:app \
  --workers "${GUNICORN_WORKERS:-4}" \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout "${GUNICORN_TIMEOUT:-120}" \
  --access-logfile - \
  --error-logfile -
