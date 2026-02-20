from rest_framework import serializers
from .models import ReportingPeriod, Report, Comment
from accounts.models import User

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
            'is_closed'
        ]
        read_only_fields = [
            'id',
            'start_date',
            'end_date',
            'deadline'
        ]

class ReportSerializer(serializers.ModelSerializer):
    """
    PRD section 6.1 - Report Fields
    Basic report serializer for list views and creating new reports
    """
    period = ReportingPeriodSerializer(read_only=True)
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    
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
        PRD section 6.2 - Report Status Lifecycle
        Validate required fields based on report status
        """
        # Only validate required fields if this is a new report or draft update
        if self.instance is None or self.instance.status == Report.Status.DRAFT:
            if not data.get('accomplishments'):
                raise serializers.ValidationError({
                    "accomplishments": "This field is required."
                })
            if not data.get('goals_next_week'):
                raise serializers.ValidationError({
                    "goals_next_week": "This field is required."
                })
            if not data.get('progress_rating'):
                raise serializers.ValidationError({
                    "progress_rating": "This field is required."
                })
        return data

class ReportDetailSerializer(ReportSerializer):
    """
    PRD section 6.1 - Report Fields
    Detailed report serializer with all fields for detail views
    """
    class Meta(ReportSerializer.Meta):
        fields = ReportSerializer.Meta.fields + [
            'blockers',
            'support_needed',
            'additional_notes'
        ]


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