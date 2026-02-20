import os
from celery import Celery
from django.conf import settings
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Configure Celery Beat schedule for periodic tasks
app.conf.beat_schedule = {
    # PRD section 6.3: Reporting Period Rules
    'create-new-reporting-period': {
        'task': 'reports.tasks.create_new_reporting_period',
        'schedule': crontab(day_of_week='monday', hour=0, minute=0),
        'options': {'queue': 'periodic'},
    },
    # PRD section 7: Notification System
    'send-weekly-reminders': {
        'task': 'notifications.tasks.send_weekly_reminders',
        'schedule': crontab(day_of_week='wed', hour=9, minute=0),
        'options': {'queue': 'periodic'},
    },
    # PRD section 7: Notification System
    'send-deadline-approaching': {
        'task': 'notifications.tasks.send_deadline_approaching',
        'schedule': crontab(day_of_week='fri', hour=9, minute=0),
        'options': {'queue': 'periodic'},
    },
    # PRD section 7: Notification System
    'send-overdue-summary': {
        'task': 'notifications.tasks.send_overdue_summary',
        'schedule': crontab(day_of_week='fri', hour=18, minute=0),
        'options': {'queue': 'periodic'},
    },
}

app.conf.timezone = 'UTC'