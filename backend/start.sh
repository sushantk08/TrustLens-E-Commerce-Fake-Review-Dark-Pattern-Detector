#!/bin/bash

# Apply database migrations
python manage.py migrate --noinput

# Start Celery in single-process mode (consumes only ~40MB RAM)
celery -A trustlens_core worker -l info --concurrency=1 -P solo --detach

# Launch Uvicorn on Render's assigned port
exec uvicorn trustlens_core.asgi:application --host 0.0.0.0 --port ${PORT:-10000} --workers 1