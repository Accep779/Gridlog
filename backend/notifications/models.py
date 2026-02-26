from django.db import models
from django.utils import timezone

class Notification(models.Model):
    """
    Stores in-app notifications as specified in PRD section 10.
    Email delivery is handled asynchronously by Celery (PRD section 7).
    """
    class NotificationType(models.TextChoices):
        REPORT_SUBMITTED = 'report_submitted', 'Report Submitted'
        COMMENT_ADDED = 'comment_added', 'Comment Added'
        COMMENT_REPLY = 'comment_reply', 'Comment Reply'
        REPORT_REVIEWED = 'report_reviewed', 'Report Reviewed'
        WEEKLY_REMINDER = 'weekly_reminder', 'Weekly Reminder'
        DEADLINE_APPROACHING = 'deadline_approaching', 'Deadline Approaching'
        OVERDUE_SUMMARY = 'overdue_summary', 'Overdue Summary'
    
    recipient = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text="The user who should receive this notification"
    )
    type = models.CharField(
        max_length=30,
        choices=NotificationType.choices,
        help_text="The type/category of notification"
    )
    message = models.CharField(
        max_length=255,
        help_text="Brief summary of the notification for display"
    )
    is_read = models.BooleanField(
        default=False,
        help_text="Whether the user has viewed this notification"
    )
    related_report = models.ForeignKey(
        'reports.Report',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Associated report, if applicable"
    )
    related_comment = models.ForeignKey(
        'reports.Comment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Associated comment, if applicable"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the notification was created"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
        ]
    
    def __str__(self):
        return f"{self.get_type_display()} for {self.recipient.email}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.save()