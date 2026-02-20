from celery import shared_task
from django.utils import timezone
from datetime import timedelta, datetime
from .models import ReportingPeriod, Report
from notifications.models import Notification
from accounts.models import AuditLog, User

@shared_task
def create_new_reporting_period():
    """
    PRD section 6.3 - Reporting Period Rules
    Creates a new reporting period every Monday (Monday to Sunday)
    """
    # Calculate dates for the new period
    today = timezone.now().date()
    
    # If today is not Monday, find the next Monday
    if today.weekday() != 0:  # Monday is 0 in Python's weekday()
        days_ahead = (7 - today.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        start_date = today + timedelta(days=days_ahead)
    else:
        start_date = today
    
    end_date = start_date + timedelta(days=6)  # Sunday
    
    # Create the new period
    period, created = ReportingPeriod.objects.get_or_create(
        start_date=start_date,
        end_date=end_date,
        defaults={
            'deadline': timezone.make_aware(
                datetime.combine(start_date + timedelta(days=4), datetime.min.time()) + 
                timedelta(hours=23, minutes=59, seconds=59)
            ),
            'is_closed': False
        }
    )
    
    if created:
        # Log the creation in audit log
        AuditLog.log(
            actor=None,  # System action
            action=AuditLog.Action.REPORT_PERIOD_CREATE,
            target=period,
            metadata={
                "message": "New reporting period auto-created",
                "start_date": str(start_date),
                "end_date": str(end_date),
                "deadline": str(period.deadline)
            }
        )
    
    # Close previous period if it exists and isn't already closed
    previous_period = ReportingPeriod.objects.filter(
        end_date__lt=start_date,
        is_closed=False
    ).order_by('-end_date').first()
    
    if previous_period:
        previous_period.is_closed = True
        previous_period.save()
        
        # Log the closing in audit log
        AuditLog.log(
            actor=None,  # System action
            action=AuditLog.Action.REPORT_PERIOD_CLOSE,
            target=previous_period,
            metadata={
                "message": "Previous reporting period closed",
                "period_id": str(previous_period.id)
            }
        )
    
    return f"Created new reporting period: {start_date} to {end_date}"