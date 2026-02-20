from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Notification
from reports.models import ReportingPeriod, Report
from accounts.models import User, AuditLog
from reports.models import Comment
from django.core.mail import send_mail
from django.conf import settings

def _send_email(recipient, subject, message):
    """Internal helper to send email notifications"""
    if not recipient.email_notifications_enabled:
        return
    
    # Prefix subject with app name
    full_subject = f"[Gridlog] {subject}"
    
    # In dev, we might not have SMTP configured - log it
    if not getattr(settings, 'EMAIL_HOST', None):
        print(f"DEBUG: Email to {recipient.email}: {full_subject}")
        return

    send_mail(
        subject=full_subject,
        message=message,
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'notifications@gridlog.com'),
        recipient_list=[recipient.email],
        fail_silently=True
    )

@shared_task
def send_weekly_reminders():
    """
    PRD section 7 - Notification System
    Sends weekly reminders to employees who haven't submitted their reports
    """
    # Get current reporting period
    current_period = ReportingPeriod.objects.filter(is_closed=False).first()
    if not current_period:
        return "No active reporting period"

    # Find employees who haven't submitted reports
    employees = User.objects.filter(
        role=User.Role.EMPLOYEE,
        reports__period=current_period,
        reports__status__in=[Report.Status.NOT_STARTED, Report.Status.DRAFT]
    ).distinct()

    # Create notifications
    count = 0
    for employee in employees:
        # Check user preferences (PRD section 7 - users may opt out)
        if not employee.email_notifications_enabled:
            continue
        if not employee.notify_on_weekly_reminder:
            continue

        Notification.objects.create(
            recipient=employee,
            type=Notification.NotificationType.WEEKLY_REMINDER,
            message="Don't forget to submit your weekly report",
            related_report=employee.reports.filter(period=current_period).first()
        )
        _send_email(
            employee, 
            "Weekly Reminder", 
            f"Hello {employee.full_name},\n\nYou haven't submitted your weekly report for the period ending {current_period.end_date}. Please log in to Gridlog to complete your submission.\n\nBest,\nGridlog Team"
        )
        count += 1

    # Log the action
    AuditLog.log(
        actor=None,  # System action
        action=AuditLog.Action.WEEKLY_REMINDER,
        metadata={
            "message": f"Weekly reminders sent to {count} employees",
            "period_id": str(current_period.id) if current_period else None
        }
    )

    return f"Weekly reminders sent to {count} employees"

@shared_task
def send_deadline_approaching():
    """
    PRD section 7 - Notification System
    Sends deadline approaching notifications to employees with pending reports
    """
    # Get current reporting period
    current_period = ReportingPeriod.objects.filter(is_closed=False).first()
    if not current_period or not current_period.deadline:
        return "No active reporting period or deadline"

    # Check if today is Friday (deadline day)
    if timezone.now().date() != current_period.deadline.date():
        return "Not deadline day"

    # Find employees who haven't submitted reports
    employees = User.objects.filter(
        role=User.Role.EMPLOYEE,
        reports__period=current_period,
        reports__status__in=[Report.Status.NOT_STARTED, Report.Status.DRAFT]
    ).distinct()

    # Create notifications
    count = 0
    for employee in employees:
        # Check user preferences (PRD section 7 - users may opt out)
        if not employee.email_notifications_enabled:
            continue
        if not employee.notify_on_deadline_approaching:
            continue

        Notification.objects.create(
            recipient=employee,
            type=Notification.NotificationType.DEADLINE_APPROACHING,
            message="Deadline approaching: Report due tonight",
            related_report=employee.reports.filter(period=current_period).first()
        )
        _send_email(
            employee,
            "Deadline Approaching",
            f"Hello {employee.full_name},\n\nThe deadline for your weekly report is tonight ({current_period.deadline.date()}). Please ensure your report is submitted on time.\n\nBest,\nGridlog Team"
        )
        count += 1

    # Log the action
    AuditLog.log(
        actor=None,  # System action
        action=AuditLog.Action.DEADLINE_APPROACHING,
        metadata={
            "message": f"Deadline approaching notifications sent to {count} employees",
            "period_id": str(current_period.id) if current_period else None
        }
    )

    return f"Deadline approaching notifications sent to {count} employees"

@shared_task
def send_overdue_summary():
    """
    PRD section 7 - Notification System
    Sends overdue report summary to supervisors
    """
    # Get current reporting period
    current_period = ReportingPeriod.objects.filter(is_closed=False).first()
    if not current_period:
        return "No active reporting period"
    
    # Find supervisors with team members who haven't submitted reports
    supervisors = User.objects.filter(
        role=User.Role.SUPERVISOR,
        team_members__reports__period=current_period,
        team_members__reports__status__in=[Report.Status.NOT_STARTED, Report.Status.DRAFT]
    ).distinct()
    
    # Create notifications for each supervisor
    count = 0
    for supervisor in supervisors:
        # Count overdue reports for this supervisor's team
        overdue_count = Report.objects.filter(
            employee__supervisor=supervisor,
            period=current_period,
            status__in=[Report.Status.NOT_STARTED, Report.Status.DRAFT]
        ).count()
        
        if overdue_count > 0:
            Notification.objects.create(
                recipient=supervisor,
                type=Notification.NotificationType.OVERDUE_SUMMARY,
                message=f"{overdue_count} team members haven't submitted reports",
                # No specific report to link to for summary notifications
            )
            count += 1
    
    # Log the action
    AuditLog.log(
        actor=None,  # System action
        action=AuditLog.Action.OVERDUE_SUMMARY,
        metadata={
            "message": f"Overdue summaries sent to {count} supervisors",
            "period_id": str(current_period.id) if current_period else None
        }
    )
    
    return f"Overdue summaries sent to {count} supervisors"

@shared_task
def send_report_submitted_notification(report_id):
    """
    PRD section 7 - Notification System
    Sends notification to supervisor when employee submits report
    """
    try:
        report = Report.objects.get(id=report_id)
        supervisor = report.employee.supervisor

        if supervisor:
            # Check supervisor notification preferences
            if supervisor.email_notifications_enabled and supervisor.notify_on_report_submitted:
                Notification.objects.create(
                    recipient=supervisor,
                    type=Notification.NotificationType.REPORT_SUBMITTED,
                    message=f"{report.employee.full_name} submitted their weekly report",
                    related_report=report
                )
                _send_email(
                    supervisor,
                    f"Report Submitted: {report.employee.full_name}",
                    f"Hello {supervisor.full_name},\n\n{report.employee.full_name} has submitted their weekly report for the period {report.period}. You can reviewer it at your earliest convenience.\n\nBest,\nGridlog Team"
                )

            # Log the action
            AuditLog.log(
                actor=report.employee,
                action=AuditLog.Action.REPORT_SUBMIT,
                target=report,
                metadata={"message": "Notification sent to supervisor"}
            )

            return f"Notification sent to supervisor {supervisor.email} about report {report_id}"
        return "No supervisor assigned"
    except Report.DoesNotExist:
        return f"Report {report_id} does not exist"

@shared_task
def send_comment_notification(comment_id):
    """
    PRD section 7 - Notification System
    Sends notification when a comment is added to a report
    """
    try:
        comment = Comment.objects.get(id=comment_id)
        report = comment.report

        # Determine who to notify
        recipients = []
        if comment.author == report.employee:
            # Employee commented - notify supervisor
            if report.employee.supervisor:
                recipients.append(report.employee.supervisor)
        else:
            # Supervisor commented - notify employee
            recipients.append(report.employee)

        # Create notifications based on user preferences
        for recipient in recipients:
            # Check notification preferences
            if not recipient.email_notifications_enabled:
                continue
            if not recipient.notify_on_comment_added:
                continue

            Notification.objects.create(
                recipient=recipient,
                type=Notification.NotificationType.COMMENT_ADDED,
                message="New comment on your report",
                related_report=report
            )
            _send_email(
                recipient,
                "New Comment",
                f"Hello {recipient.full_name},\n\nA new comment has been added to the report for period {report.period} by {comment.author.full_name}.\n\nMessage: \"{comment.content[:200]}...\"\n\nBest,\nGridlog Team"
            )

        # Log the action
        AuditLog.log(
            actor=comment.author,
            action=AuditLog.Action.COMMENT_ADD,
            target=report,
            metadata={
                "message": "Comment notification sent",
                "comment_id": str(comment_id)
            }
        )

        return f"Comment notifications sent for comment {comment_id}"
    except Comment.DoesNotExist:
        return f"Comment {comment_id} does not exist"

@shared_task
def send_report_reviewed_notification(report_id):
    """
    PRD section 7 - Notification System
    Sends notification to employee when supervisor marks report as reviewed
    """
    try:
        report = Report.objects.get(id=report_id)
        employee = report.employee

        # Check employee notification preferences
        if employee.email_notifications_enabled and employee.notify_on_report_reviewed:
            Notification.objects.create(
                recipient=employee,
                type=Notification.NotificationType.REPORT_REVIEWED,
                message="Your report has been reviewed",
                related_report=report
            )
            _send_email(
                employee,
                "Report Reviewed",
                f"Hello {employee.full_name},\n\nYour weekly report for the period {report.period} has been marked as REVIEWED by your supervisor.\n\nBest,\nGridlog Team"
            )

        # Log the action
        AuditLog.log(
            actor=report.employee.supervisor,
            action=AuditLog.Action.REPORT_REVIEW,
            target=report,
            metadata={"message": "Notification sent to employee"}
        )

        return f"Notification sent to employee {report.employee.email} about report {report_id}"
    except Report.DoesNotExist:
        return f"Report {report_id} does not exist"