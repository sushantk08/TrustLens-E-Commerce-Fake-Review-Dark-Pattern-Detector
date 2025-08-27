#!/bin/bash

# Apply database migrations
python manage.py migrate --noinput

# Start Celery in a single process to keep memory under 200MB
celery -A trustlens_core worker -l info --concurrency=1 -P solo --detach

# Launch Daphne ASGI server immediately so Render detects the open port
exec daphne -b 0.0.0.0 -p ${PORT:-10000} trustlens_core.asgi:application