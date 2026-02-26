from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone

class UserManager(BaseUserManager):
    def create_user(self, email, full_name, role, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, full_name=full_name, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.Role.ADMIN)
        return self.create_user(email, full_name, password=password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        EMPLOYEE = 'employee', 'Employee'
        SUPERVISOR = 'supervisor', 'Supervisor'
        ADMIN = 'admin', 'Admin'

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=Role.choices)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    supervisor = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='team_members'
    )
    # Add this field to the User model class
    password_reset_required = models.BooleanField(
        default=True,
        help_text="Indicates if user needs to reset password on first login"
    )
    # Notification preferences (PRD section 7)
    email_notifications_enabled = models.BooleanField(
        default=True,
        help_text="Whether to receive email notifications"
    )
    notify_on_report_submitted = models.BooleanField(
        default=True,
        help_text="Notify when employee submits a report"
    )
    notify_on_comment_added = models.BooleanField(
        default=True,
        help_text="Notify when a comment is added to your report"
    )
    notify_on_report_reviewed = models.BooleanField(
        default=True,
        help_text="Notify when your report is reviewed"
    )
    notify_on_weekly_reminder = models.BooleanField(
        default=True,
        help_text="Receive weekly reminders to submit reports"
    )
    notify_on_deadline_approaching = models.BooleanField(
        default=True,
        help_text="Receive deadline approaching notifications"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'role']

    def __str__(self):
        return self.email
    
class AuditLog(models.Model):
    class Action(models.TextChoices):
        LOGIN = 'login', 'User Login'
        LOGOUT = 'logout', 'User Logout'
        PASSWORD_CHANGE = 'password_change', 'Password Change'
        USER_CREATE = 'user_create', 'User Created'
        USER_UPDATE = 'user_update', 'User Updated'
        USER_DEACTIVATE = 'user_deactivate', 'User Deactivated'
        REPORT_SUBMIT = 'report_submit', 'Report Submitted'
        REPORT_REVIEW = 'report_review', 'Report Reviewed'
        COMMENT_ADD = 'comment_add', 'Comment Added'
        REPORT_PERIOD_CREATE = 'report_period_create', 'Reporting Period Created'
        REPORT_PERIOD_CLOSE = 'report_period_close', 'Reporting Period Closed'
        REPORT_PERIOD_REOPEN = 'report_period_reopen', 'Reporting Period Reopened'
        REPORT_REVISION_REQUESTED = 'report_revision_requested', 'Report Revision Requested'
    
    actor = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    action = models.CharField(
        max_length=30,
        choices=Action.choices
    )
    target_model = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )
    target_id = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )
    metadata = models.JSONField(
        null=True,
        blank=True
    )
    timestamp = models.DateTimeField(
        default=timezone.now
    )
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['action']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.get_action_display()} by {self.actor or 'System'} at {self.timestamp}"
    
    @classmethod
    def log(cls, actor, action, target=None, metadata=None):
        target_model = None
        target_id = None
        
        if target:
            target_model = target._meta.model_name
            target_id = str(target.pk)
        
        return cls.objects.create(
            actor=actor,
            action=action,
            target_model=target_model,
            target_id=target_id,
            metadata=metadata
        )    