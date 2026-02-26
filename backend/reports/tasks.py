from celery import shared_task
from django.utils import timezone
from datetime import timedelta, datetime
from django.db import transaction
from .models import ReportingPeriod, Report
from notifications.models import Notification
from accounts.models import AuditLog, User

@shared_task
@transaction.atomic
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
    
    # Close previous periods if they exist and aren't already closed
    # Using .update() is more efficient, but we fetch them first to log them
    previous_periods_list = list(ReportingPeriod.objects.filter(
        end_date__lt=start_date,
        is_closed=False
    ))
    
    count = len(previous_periods_list)
    if count > 0:
        # Perform mass update
        ReportingPeriod.objects.filter(
            id__in=[p.id for p in previous_periods_list]
        ).update(is_closed=True)
        
        # Log the closing in audit log
        for p in previous_periods_list:
            AuditLog.log(
                actor=None,  # System action
                action=AuditLog.Action.REPORT_PERIOD_CLOSE,
                target=p,
                metadata={
                    "message": "Previous reporting period closed",
                    "period_id": str(p.id)
                }
            )
    
    return f"Created new reporting period ({start_date} to {end_date}) and closed {count} old periods."

@shared_task
@transaction.atomic
def auto_close_reporting_periods():
    """
    Finds reporting periods that have passed their 'closes_at' time
    but are still marked as open, and closes them.
    """
    now = timezone.now()
    periods_to_close = ReportingPeriod.objects.filter(
        is_closed=False,
        closes_at__lte=now
    )
    
    count = periods_to_close.count()
    if count > 0:
        for period in periods_to_close:
            period.is_closed = True
            period.save()
            
            # Log the closing in audit log
            AuditLog.log(
                actor=None,  # System action
                action=AuditLog.Action.PERIOD_CLOSE,
                target=period,
                metadata={
                    "message": "Reporting period automatically closed by scheduled timeline",
                    "period_id": period.id,
                    "closed_at": str(now)
                }
            )
            
    return f"Automatically closed {count} reporting periods based on schedule."