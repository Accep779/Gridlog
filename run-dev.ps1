# Gridlog Development Environment Startup Script (Windows PowerShell)

Write-Host "Starting Gridlog development environment (Monorepo)..." -ForegroundColor Cyan

# Ensure Redis is running
Write-Host "Checking if Redis is running on localhost:6379..." -ForegroundColor Yellow
$redisCheck = Get-NetTCPConnection -LocalPort 6379 -ErrorAction SilentlyContinue
if (-not $redisCheck) {
    Write-Host "WARNING: Redis does not appear to be running on port 6379. Background tasks may fail." -ForegroundColor Red
} else {
     Write-Host "Redis is running." -ForegroundColor Green
}

# Define paths
$root = Get-Location
$backendPath = Join-Path $root "backend"
$frontendPath = Join-Path $root "frontend"

# Start Django Backend
Write-Host "Starting Django development server..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd $backendPath; .\.venv\Scripts\python.exe manage.py runserver"

# Start Celery Worker
Write-Host "Starting Celery worker..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd $backendPath; .\.venv\Scripts\python.exe -m celery -A config worker -l INFO -Q default,periodic -P solo"

# Start Celery Beat
Write-Host "Starting Celery beat scheduler..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd $backendPath; .\.venv\Scripts\python.exe -m celery -A config beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler --pidfile="

# Start Frontend
Write-Host "Starting Frontend development server..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd $frontendPath; npm run dev"

Write-Host "All services have been triggered in separate terminal windows." -ForegroundColor Green
