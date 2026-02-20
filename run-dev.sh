#!/bin/bash
echo "Starting Gridlog development environment..."

# Open a new terminal tab for Redis (if not already running)
echo "Ensure Redis is running (localhost:6379)"
echo "If not, start it with: redis-server"

# Open a new terminal tab for Celery Beat
echo "Starting Celery Beat scheduler..."
celery -A config beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler &

# Open a new terminal tab for Celery Worker
echo "Starting Celery worker..."
celery -A config worker -l INFO -Q default,periodic &

# Run Django development server
echo "Starting Django development server..."
python manage.py runserver

# Clean up background processes when script exits
trap 'kill $(jobs -p)' EXIT