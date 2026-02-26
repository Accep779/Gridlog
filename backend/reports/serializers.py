from rest_framework import serializers
from .models import ReportingPeriod, Report, Comment
from accounts.models import User
from .utils import sanitize_html

class ReportingPeriodSerializer(serializers.ModelSerializer):
    """
    PRD section 6.3 - Reporting Period Rules
    Serializes reporting period data
    """
    class Meta:
        model = ReportingPeriod
        fields = [
            'id',
            'start_date',
            'end_date',
            'deadline',
            'closes_at',
            'is_closed'
        ]
        read_only_fields = [
            'id',
            'start_date',
            'end_date'
        ]

class ReportSerializer(serializers.ModelSerializer):
    """
    PRD section 6.1 - Report Fields
    Basic report serializer for list views and creating new reports
    """
    period = ReportingPeriodSerializer(read_only=True)
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    
    # Explicitly define fields to allow blank/null for drafts
    accomplishments = serializers.CharField(allow_blank=True, required=False)
    goals_next_week = serializers.CharField(allow_blank=True, required=False)
    progress_rating = serializers.CharField(allow_blank=True, required=False, allow_null=True)
    blockers = serializers.CharField(allow_blank=True, required=False)
    support_needed = serializers.CharField(allow_blank=True, required=False)
    additional_notes = serializers.CharField(allow_blank=True, required=False)

    class Meta:
        model = Report
        fields = [
            'id',
            'employee',
            'employee_name',  
            'period',
            'status',
            'accomplishments',
            'goals_next_week',
            'progress_rating',
            'blockers',
            'support_needed',
            'additional_notes',
            'is_late',
            'submitted_at',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'employee',
            'period',
            'status',
            'is_late',
            'submitted_at',
            'created_at',
            'updated_at'
        ]
    
    def validate(self, data):
        """
        Validation for reports.
        Sanitizes rich text fields server-side (PRD section 6.1).
        Strict submission validation is handled in the ViewSet 'submit' action
        to allow partial draft saving (PRD section 6.2).
        """
        rich_text_fields = ['accomplishments', 'goals_next_week', 'blockers']
        for field in rich_text_fields:
            if field in data and data[field]:
                data[field] = sanitize_html(data[field])
        return data

class ReportDetailSerializer(ReportSerializer):
    """
    PRD section 6.1 - Report Fields
    Detailed report serializer with all fields for detail views
    """
    class Meta(ReportSerializer.Meta):
        pass


class RejectReportSerializer(serializers.Serializer):
    """
    Serializer for validating report rejection feedback
    """
    feedback = serializers.CharField(
        min_length=10,
        max_length=2000,
        error_messages={
            'min_length': 'Feedback must be at least 10 characters.',
            'max_length': 'Feedback cannot exceed 2000 characters.'
        }
    )

class CommentSerializer(serializers.ModelSerializer):
    """
    PRD section 7 - Notification System
    Serializes comment data with one-level reply threading
    """
    author = serializers.StringRelatedField()
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id',
            'author',
            'body',
            'created_at',
            'parent',
            'replies'
        ]
        read_only_fields = [
            'id',
            'author',
            'created_at'
        ]
    
    def get_replies(self, obj):
        """
        PRD section 13 - Out of Scope: "Reply threading beyond one level is not supported in v1"
        Only return direct replies (one level of threading)
        """
        replies = obj.replies.all()
        return CommentSerializer(replies, many=True).data
    
    def validate(self, data):
        """
        Ensure one-level threading as specified in PRD
        """
        parent = data.get('parent')
        if parent and parent.parent:
            raise serializers.ValidationError(
                "Reply threading beyond one level is not supported in v1"
            )
        return data
    
    def create(self, validated_data):
        """
        PRD section 7 - Notification System
        Auto-create notification when comment is added
        """
        comment = super().create(validated_data)
        
        # Create notification (will be implemented fully in notifications milestone)
        # TODO: Implement notification creation
        
        return comment