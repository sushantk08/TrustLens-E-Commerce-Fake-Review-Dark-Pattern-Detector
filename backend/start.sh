#!/bin/bash

# Apply database migrations
python manage.py migrate --noinput

# Start Celery in the background
celery -A trustlens_core worker -l info --concurrency=1 -P solo --detach

# Launch production ASGI server with Uvicorn
exec uvicorn trustlens_core.asgi:application --host 0.0.0.0 --port ${PORT:-10000} --workers 1