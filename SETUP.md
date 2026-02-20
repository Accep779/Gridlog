# Gridlog - Setup & Requirements Document

Welcome to the Gridlog project! This document outlines the prerequisites and step-by-step instructions required for anyone to install the dependencies and run the application locally.

## Prerequisites
Before you begin, ensure you have the following installed on your system:
- **Python 3.10+** (for the Django backend)
- **Node.js 18+** & **npm** (for the Quasar/Vue frontend)
- **Redis** (required for Celery task queuing and scheduling)
- **Git** (to clone the repository)
- **MySQL / MariaDB** *(Optional: The app is configured for MySQL in `.env.example`, but Django will fall back to `db.sqlite3` for local development if not provided.)*

---

## 1. Initial Setup
Clone the repository and navigate into the project directory:
```bash
git clone <repository_url>
cd Gridlog
```

---

## 2. Backend Setup (Django)
The backend is built with Django, Django REST Framework, and Celery. 

1. **Create and Activate a Virtual Environment**
   - **Windows:**
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\activate
     ```
   - **macOS / Linux:**
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

2. **Install Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**
   - Copy the example environment file to `.env`:
     - **Windows:** `copy .env.example .env`
     - **macOS / Linux:** `cp .env.example .env`
   - Open the `.env` file and generate a secret key using the following command, then paste it into `DJANGO_SECRET_KEY`:
     ```bash
     python -c "import secrets; print(secrets.token_urlsafe(50))"
     ```

4. **Run Database Migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create an Admin Account (Superuser)**
   You can create one interactively or use the provided script:
   ```bash
   python manage.py createsuperuser
   # OR use the provided automated script:
   python create_superuser.py
   ```

---

## 3. Frontend Setup (Quasar / Vue 3)
The frontend is located at the root directory and powered by the Quasar CLI.

1. **Install Node Dependencies**
   ```bash
   npm install
   ```

---

## 4. Running the Development Environment
Gridlog requires several processes to run simultaneously for full functionality. Open **separate terminal windows** for each of the following (ensure the Python virtual environment is activated for backend commands):

### Terminal 1: Redis
Start your Redis server. This must be running for background tasks to work.
```bash
redis-server
```

### Terminal 2: Celery Worker
This processes background jobs like report generation or notifications.
```bash
celery -A config worker -l INFO -Q default,periodic
```

### Terminal 3: Celery Beat (Scheduler)
This schedules periodic tasks.
```bash
celery -A config beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### Terminal 4: Django Backend Server
```bash
python manage.py runserver
```
*(The backend runs on `http://localhost:8000`)*

### Terminal 5: Quasar Frontend Server
```bash
npm run dev
# OR
npx quasar dev
```
*(The frontend usually runs on `http://localhost:9000`)*

---

### *Alternative for macOS/Linux Users:*
You can simply run the provided bash script to start the Django backend, Celery worker, and Celery beat automatically in the background:
```bash
chmod +x run-dev.sh
./run-dev.sh
```
*(You will still need to run `npm run dev` in a separate terminal for the frontend).*
