from rest_framework import serializers
from .models import Notification
from reports.serializers import ReportSerializer

class NotificationSerializer(serializers.ModelSerializer):
    """
    PRD section 7 - Notification System and section 10 - Data Model Overview
    Serializes notification data for in-app notifications
    """
    related_report = ReportSerializer(read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id',
            'type',
            'message',
            'is_read',
            'related_report',
            'created_at'
        ]
        read_only_fields = [
            'id',
            'type',
            'message',
            'related_report',
            'created_at'
        ]
    
    def to_representation(self, instance):
        """
        PRD section 7 - Notification System
        Customize notification display format based on type
        """
        representation = super().to_representation(instance)
        
        # Customize message based on notification type
        if instance.type == Notification.NotificationType.REPORT_SUBMITTED:
            representation['message'] = f"{instance.related_report.employee.full_name} submitted their weekly report"
        elif instance.type == Notification.NotificationType.COMMENT_ADDED:
            representation['message'] = "New comment on your report"
        elif instance.type == Notification.NotificationType.COMMENT_REPLY:
            representation['message'] = "Reply to your comment"
        elif instance.type == Notification.NotificationType.REPORT_REVIEWED:
            representation['message'] = "Your report has been reviewed"
        elif instance.type == Notification.NotificationType.WEEKLY_REMINDER:
            representation['message'] = "Don't forget to submit your weekly report"
        elif instance.type == Notification.NotificationType.DEADLINE_APPROACHING:
            representation['message'] = "Deadline approaching: Report due tonight"
        elif instance.type == Notification.NotificationType.OVERDUE_SUMMARY:
            representation['message'] = "Overdue reports summary available"
            
        return representation