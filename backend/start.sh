#!/bin/bash

# 1. Run migrations and start Celery asynchronously in background
(
  echo "Applying database migrations in background..."
  python manage.py migrate --noinput
  echo "Starting Celery worker in background..."
  celery -A trustlens_core worker -l info --concurrency=1 -P solo
) &

# 2. Launch Uvicorn immediately so Render detects port 10000 in < 2 seconds
echo "Launching Uvicorn ASGI server on port ${PORT:-10000}..."
exec uvicorn trustlens_core.asgi:application --host 0.0.0.0 --port ${PORT:-10000} --workers 1