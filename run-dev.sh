#!/bin/bash
echo "Starting Gridlog development environment (Monorepo)..."

# Navigate to backend and run services
cd backend || exit

# Open a new terminal tab for Redis (if not already running)
echo "Ensure Redis is running (localhost:6379)"

# Start Celery Beat scheduler
echo "Starting Celery Beat scheduler..."
celery -A config beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler &

# Start Celery worker
echo "Starting Celery worker..."
celery -A config worker -l INFO -Q default,periodic &

# Run Django development server
echo "Starting Django development server..."
python manage.py runserver &

# Navigate back to root and then to frontend
cd ../frontend || exit

# Run Frontend development server
echo "Starting Frontend development server..."
npm run dev

# Clean up background processes when script exits
trap 'kill $(jobs -p)' EXIT