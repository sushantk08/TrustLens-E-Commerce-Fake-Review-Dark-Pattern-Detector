#!/bin/bash

# Apply database migrations
python manage.py migrate --noinput

# Start Celery worker in the background (detached)
celery -A trustlens_core worker -l info --detach

# Start Daphne ASGI server in the foreground using Render's dynamic PORT
exec daphne -b 0.0.0.0 -p ${PORT:-8000} trustlens_core.asgi:application