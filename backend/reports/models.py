from django.db import models
from django.utils import timezone
from datetime import timedelta, datetime
from django.db import models
from django.core.validators import MaxLengthValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta

class ReportingPeriodManager(models.Manager):
    def current_period(self):
        """Return the active reporting period (not closed)"""
        return self.filter(is_closed=False).first()

class ReportingPeriod(models.Model):
    """
    Represents a single reporting period (Monday to Sunday)
    Auto-generated each Monday by Celery task as per PRD section 6.3
    """
    start_date = models.DateField(
        help_text="Monday of the reporting week"
    )
    end_date = models.DateField(
        help_text="Sunday of the reporting week"
    )
    deadline = models.DateTimeField(
        default=timezone.make_aware(
            datetime.combine(timezone.now().date(), datetime.min.time()) + 
            timedelta(hours=23, minutes=59, seconds=59)
        ),
        help_text="Submission deadline (Friday 11:59 PM)"
    )
    is_closed = models.BooleanField(
        default=False,
        help_text="Indicates if the period is closed to new submissions"
    )
    closes_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Scheduled datetime to automatically close the period"
    )
    
    objects = ReportingPeriodManager()
    
    class Meta:
        ordering = ['-start_date']
        unique_together = ['start_date', 'end_date']
        verbose_name = "Reporting Period"
        verbose_name_plural = "Reporting Periods"
    
    def __str__(self):
        return f"{self.start_date} to {self.end_date}"
    
    def save(self, *args, **kwargs):
        """Ensure deadline is set to Friday 11:59 PM of the reporting week"""
        if not self.deadline:
            # Calculate Friday of this period (Monday + 4 days)
            friday = self.start_date + timedelta(days=4)
            self.deadline = timezone.make_aware(
                datetime.combine(friday, datetime.min.time()) + 
                timedelta(hours=23, minutes=59, seconds=59)
            )
        super().save(*args, **kwargs)
    
    @property
    def is_actually_closed(self):
        """Check if the period is closed either manually or by timeline"""
        if self.is_closed:
            return True
        if self.closes_at and timezone.now() >= self.closes_at:
            return True
        return False

    @property
    def is_current(self):
        """Check if this is the current active period"""
        return not self.is_actually_closed and self.start_date <= timezone.now().date() <= self.end_date



class Report(models.Model):
    """
    The core entity of Gridlog - represents an employee's weekly report.
    Implements the 7-field schema specified in PRD section 6.1.
    """
    
    class Status(models.TextChoices):
        NOT_STARTED = 'not_started', 'Not Started'
        DRAFT = 'draft', 'Draft'
        REVISION_REQUESTED = 'revision_requested', 'Revision Requested'
        SUBMITTED = 'submitted', 'Submitted'
        REVIEWED = 'reviewed', 'Reviewed'
    
    class ProgressRating(models.TextChoices):
        ON_TRACK = 'on_track', 'On Track'
        AT_RISK = 'at_risk', 'At Risk'
        BEHIND = 'behind', 'Behind'
        COMPLETED_EARLY = 'completed_early', 'Completed Early'
    
    employee = models.ForeignKey(
        'accounts.User', 
        on_delete=models.CASCADE,
        related_name='reports',
        help_text="The employee who submitted this report"
    )
    period = models.ForeignKey(
        'reports.ReportingPeriod', 
        on_delete=models.CASCADE,
        related_name='reports',
        help_text="The reporting period this report belongs to"
    )
    status = models.CharField(
        max_length=20, 
        choices=Status.choices, 
        default=Status.DRAFT,  # CHANGED FROM NOT_STARTED TO DRAFT
        help_text="Current state in the report lifecycle"
    )
    accomplishments = models.TextField(
        validators=[MaxLengthValidator(3000)],
        blank=True,
        help_text="Accomplishments from the current week (required)"
    )
    goals_next_week = models.TextField(
        validators=[MaxLengthValidator(2000)],
        blank=True,
        help_text="Goals for the upcoming week (required)"
    )
    blockers = models.TextField(
        validators=[MaxLengthValidator(1500)],
        blank=True,
        help_text="Blockers and challenges faced this week"
    )
    support_needed = models.CharField(
        max_length=1000,
        blank=True,
        help_text="Specific support needed from the supervisor"
    )
    progress_rating = models.CharField(
        max_length=20,
        choices=ProgressRating.choices,
        blank=True,
        help_text="Overall progress rating for the week"
    )
    additional_notes = models.CharField(
        max_length=1000,
        blank=True,
        help_text="Additional notes for the supervisor"
    )
    is_late = models.BooleanField(
        default=False,
        help_text="Indicates if the report was submitted after the deadline"
    )
    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when the report was submitted"
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when the report was marked as reviewed"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the report was first created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp of the last update to the report"
    )
    
    class Meta:
        unique_together = ['employee', 'period']
        ordering = ['-period__start_date']
        verbose_name = "Report"
        verbose_name_plural = "Reports"
        indexes = [
            models.Index(fields=['employee', 'status']),
            models.Index(fields=['period', 'status']),
        ]
    
    def __str__(self):
        return f"Report for {self.employee.full_name} - {self.period.start_date} to {self.period.end_date}"
    
    def save(self, *args, **kwargs):
        """Ensure proper status transitions and late flagging"""
        # Calculate if report is late
        if self.submitted_at and self.period.deadline:
            self.is_late = self.submitted_at > self.period.deadline
        
        # Ensure required fields are populated for submitted reports
        if self.status == self.Status.SUBMITTED:
            if not self.accomplishments or not self.goals_next_week or not self.progress_rating:
                raise ValueError("Accomplishments, goals_next_week, and progress_rating are required for submitted reports")
        
        super().save(*args, **kwargs)
    
    def can_edit(self):
        """Check if the report can still be edited by the employee"""
        return self.status in [self.Status.DRAFT, self.Status.REVISION_REQUESTED] and not self.period.is_actually_closed
    
    def mark_submitted(self):
        """Transition report to Submitted status"""
        if self.status not in [self.Status.NOT_STARTED, self.Status.DRAFT]:
            raise ValueError("Only draft reports can be submitted")
        
        self.status = self.Status.SUBMITTED
        self.submitted_at = timezone.now()
        self.save()
    
    def mark_reviewed(self):
        """Transition report to Reviewed status"""
        if self.status != self.Status.SUBMITTED:
            raise ValueError("Only submitted reports can be marked as reviewed")

        self.status = self.Status.REVIEWED
        self.reviewed_at = timezone.now()
        self.save()
    
    @property
    def is_current_period(self):
        """Check if this report is for the current active period"""
        return self.period.is_current    


class Comment(models.Model):
    """
    Represents a comment on a report. Supports one-level reply threading as specified in PRD section 10.
    """
    
    report = models.ForeignKey(
        'reports.Report',
        on_delete=models.CASCADE,
        related_name='comments',
        help_text="The report this comment belongs to"
    )
    
    author = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='comments',
        help_text="The user who created this comment"
    )
    
    body = models.TextField(
        validators=[MaxLengthValidator(2000)],
        help_text="Comment content (plain text in v1)"
    )
    
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        help_text="Parent comment for threading (one-level only in v1)"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the comment was created"
    )
    
    class Meta:
        ordering = ['created_at']
        verbose_name = "Comment"
        verbose_name_plural = "Comments"
        indexes = [
            models.Index(fields=['report']),
            models.Index(fields=['author']),
        ]
    
    def __str__(self):
        return f"Comment by {self.author.email} on {self.report}"
    
    def clean(self):
        """Ensure we only allow one level of threading (PRD section 13 - Out of Scope)"""
        if self.parent and self.parent.parent:
            raise ValidationError("Reply threading beyond one level is not supported in v1")
        super().clean()