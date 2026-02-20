from rest_framework import serializers
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from .models import User

class LoginSerializer(serializers.Serializer):
    """
    PRD section 5.1 - Authentication & Access Control
    Validates email and password for login
    """
    email = serializers.EmailField()
    password = serializers.CharField(style={'input_type': 'password'}, write_only=True)
    
    def validate(self, data):
        """
        Validate the email and password
        """
        email = data.get('email')
        password = data.get('password')
        
        if email and password:
            user = authenticate(email=email, password=password)
            
            if user:
                if not user.is_active:
                    raise ValidationError("Account is deactivated")
                
                data['user'] = user
                return data
            else:
                raise ValidationError("Invalid credentials")
        else:
            raise ValidationError("Email and password are required")
        
class UserProfileSerializer(serializers.ModelSerializer):
    """
    PRD section 9.3 - Key API Endpoints
    Serializes user profile data for the /me/ endpoint
    """
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'full_name',
            'role',
            'is_active',
            'created_at',
            'email_notifications_enabled',
            'notify_on_report_submitted',
            'notify_on_comment_added',
            'notify_on_report_reviewed',
            'notify_on_weekly_reminder',
            'notify_on_deadline_approaching'
        ]
        read_only_fields = [
            'id',
            'email',
            'role',
            'created_at'
        ]

    def update(self, instance, validated_data):
        """
        Update user profile information
        Only full_name and is_active (for admins) can be updated
        """
        # Only admins can update is_active status
        if 'is_active' in validated_data and not self.context['request'].user.role == User.Role.ADMIN:
            raise serializers.ValidationError({"is_active": "Only admins can deactivate accounts"})

        instance.full_name = validated_data.get('full_name', instance.full_name)

        # Admins can update is_active status
        if self.context['request'].user.role == User.Role.ADMIN and 'is_active' in validated_data:
            instance.is_active = validated_data['is_active']

        # Update notification preferences
        notification_fields = [
            'email_notifications_enabled',
            'notify_on_report_submitted',
            'notify_on_comment_added',
            'notify_on_report_reviewed',
            'notify_on_weekly_reminder',
            'notify_on_deadline_approaching'
        ]
        for field in notification_fields:
            if field in validated_data:
                setattr(instance, field, validated_data[field])

        instance.save()
        return instance 
 
 
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

class PasswordResetSerializer(serializers.Serializer):
    """
    PRD section 5.1 - Authentication & Access Control
    Handles forced password reset on first login
    """
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        """
        Validate password meets complexity requirements
        PRD section 8: Minimum 8 characters; at least 1 uppercase, 1 number, 1 special character
        """
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)

        # Additional custom validation for PRD requirements
        if not any(c.isupper() for c in value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in value):
            raise serializers.ValidationError("Password must contain at least one number")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in value):
            raise serializers.ValidationError("Password must contain at least one special character")

        return value


class UserCreationSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new users (admin only)
    """
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'full_name', 'role', 'password', 'confirm_password', 'is_active']

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match"})
        return data

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)
        if not any(c.isupper() for c in value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in value):
            raise serializers.ValidationError("Password must contain at least one number")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in value):
            raise serializers.ValidationError("Password must contain at least one special character")
        return value

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        user = User.objects.create_user(
            email=validated_data['email'],
            full_name=validated_data.get('full_name', ''),
            role=validated_data.get('role', User.Role.EMPLOYEE),
            password=password,
            is_active=validated_data.get('is_active', True)
        )
        return user


class BulkUserImportSerializer(serializers.Serializer):
    """
    PRD section 5.4 - Admin Panel
    Handles bulk CSV import for 300+ user onboarding
    """
    csv_file = serializers.FileField()

    def validate_csv_file(self, value):
        if not value.name.endswith('.csv'):
            raise serializers.ValidationError("File must be a CSV file")
        if value.size > 5 * 1024 * 1024:  # 5MB limit
            raise serializers.ValidationError("File size must be less than 5MB")
        return value


class BulkUserImportResultSerializer(serializers.Serializer):
    """Serializer for bulk import results"""
    success_count = serializers.IntegerField()
    error_count = serializers.IntegerField()
    errors = serializers.ListField(child=serializers.CharField())     