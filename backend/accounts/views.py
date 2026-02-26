from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from django.contrib.auth import authenticate
from functools import wraps
import logging
from .serializers import LoginSerializer, PasswordResetSerializer, UserProfileSerializer, UserCreationSerializer, BulkUserImportSerializer, BulkUserImportResultSerializer
from .models import User, AuditLog
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
import csv
import io
from django.db import transaction

logger = logging.getLogger(__name__)


def require_password_reset_not_required(view_func):
    """
    Decorator to check that password reset is not required before allowing access.
    Used for UserProfileView methods that require a completed password reset.
    """
    @wraps(view_func)
    def wrapper(self, request, *args, **kwargs):
        if request.user.password_reset_required:
            return Response(
                {"error": "Password reset required"},
                status=status.HTTP_403_FORBIDDEN
            )
        return view_func(self, request, *args, **kwargs)
    return wrapper


class AuditLogPagination(PageNumberPagination):
    """Pagination for audit log list endpoints"""
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100

class LoginView(APIView):
    """
    PRD section 5.1 - Authentication & Access Control
    Returns JWT tokens upon successful authentication
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        user = authenticate(email=email, password=password)
        
        if not user:
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not user.is_active:
            return Response(
                {"error": "Account is deactivated"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role,
                'password_reset_required': user.password_reset_required
            }
        })


class CustomTokenRefreshView(TokenRefreshView):
    """
    PRD section 5.1 - Authentication & Access Control
    Returns a new access token using a valid refresh token
    """
    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except InvalidToken:
            return Response(
                {"error": "Invalid or expired refresh token"},
                status=status.HTTP_401_UNAUTHORIZED
            )    


class LogoutView(APIView):
    """
    PRD section 5.1 - Authentication & Access Control
    Blacklists the refresh token to prevent further use
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Validate refresh token is provided
        try:
            refresh_token = request.data["refresh"]
        except KeyError:
            return Response(
                {"error": "Refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            logger.info(f"User {request.user.email} logged out successfully")
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except InvalidToken:
            return Response(
                {"error": "Invalid token"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Logout error for user {request.user.email}: {str(e)}")
            return Response(
                {"error": "An error occurred during logout"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )    


class UserProfileView(APIView):
    """
    PRD section 5.1 - Authentication & Access Control
    Returns the current user's profile information
    """
    permission_classes = [IsAuthenticated]

    @require_password_reset_not_required
    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    @require_password_reset_not_required
    def put(self, request):
        data = request.data.copy()
        # PRD requirement: in-app notifications cannot be disabled by users
        data.pop('in_app_notifications_enabled', None)

        serializer = UserProfileSerializer(
            request.user,
            data=data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InitialPasswordResetView(APIView):
    """
    PRD section 5.1 - Authentication & Access Control
    Handles forced password reset on first login
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Check if user needs password reset
        if not request.user.password_reset_required:
            return Response(
                {"error": "Password reset not required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Set new password
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.password_reset_required = False
        request.user.save()
        
        # Log the password change in audit log
        AuditLog.log(
            actor=request.user,
            action=AuditLog.Action.PASSWORD_CHANGE,
            metadata={"message": "Initial password set"}
        )
        
        return Response({"message": "Password successfully reset"})


class UserViewSet(viewsets.ModelViewSet):
    """
    PRD section 5.1 & 9.3
    Enables supervisor/admin to list and manage users
    """
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'put', 'patch', 'head', 'options']

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreationSerializer
        return UserProfileSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.SUPERVISOR:
            return User.objects.filter(role=User.Role.EMPLOYEE, supervisor=user)
        elif user.role == User.Role.ADMIN:
            return User.objects.all()
        return User.objects.filter(id=user.id)



    def perform_update(self, serializer):
        """
        Custom update logic to handle:
        1. Strict role checks for is_active (Admin only)
        2. Session revocation on deactivation
        3. Detailed diff-based audit logging
        """
        user = self.get_object()
        old_data = {
            'is_active': user.is_active,
            'role': user.role,
            'supervisor': user.supervisor.id if user.supervisor else None,
            'full_name': user.full_name,
            'email': user.email
        }
        
        # Check if is_active is being changed and by whom
        new_active = serializer.validated_data.get('is_active')
        if new_active is not None and new_active != user.is_active:
            if self.request.user.role != User.Role.ADMIN:
                raise permissions.PermissionDenied("Only admins can change user active status")
        
        with transaction.atomic():
            print(f"DEBUG: Saving serializer with data: {serializer.validated_data}")
            serializer.save()
            new_user = serializer.instance
            
            # Identify changes for logging
            diff = {}
            for field, old_val in old_data.items():
                new_val = getattr(new_user, field)
                if field == 'supervisor':
                    new_val = new_user.supervisor.id if new_user.supervisor else None
                
                if old_val != new_val:
                    diff[field] = {'from': old_val, 'to': new_val}
            
            if diff:
                action = AuditLog.Action.USER_UPDATE
                if 'is_active' in diff:
                    action = AuditLog.Action.USER_DEACTIVATE if not new_user.is_active else AuditLog.Action.USER_UPDATE
                
                AuditLog.log(
                    actor=self.request.user,
                    action=action,
                    target=new_user,
                    metadata={"changes": diff, "message": f"User account updated: {list(diff.keys())}"}
                )
            
            # If deactivated, revoke all sessions
            if new_active is False:
                tokens = OutstandingToken.objects.filter(user=new_user)
                for token in tokens:
                    BlacklistedToken.objects.get_or_create(token=token)
                logger.info(f"Revoked all sessions for deactivated user: {new_user.email}")


    @action(detail=False, methods=['get'])
    def employees(self, request):
        """Returns list of employees for assignment or viewing"""
        employees = User.objects.filter(role=User.Role.EMPLOYEE)
        serializer = self.get_serializer(employees, many=True)
        return Response(serializer.data)



class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    PRD tracking of sensitive actions
    """
    queryset = AuditLog.objects.all()
    permission_classes = [IsAuthenticated]
    pagination_class = AuditLogPagination

    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.ADMIN:
            qs = AuditLog.objects.all()
        elif user.role == User.Role.SUPERVISOR:
            qs = AuditLog.objects.filter(actor__role=User.Role.EMPLOYEE)
        else:
            qs = AuditLog.objects.filter(actor=user)

        search = self.request.query_params.get('search', '').strip()
        if search:
            from django.db.models import Q
            qs = qs.filter(
                Q(actor__full_name__icontains=search) |
                Q(action__icontains=search)
            )

        action_filter = self.request.query_params.get('action', '').strip()
        if action_filter:
            qs = qs.filter(action=action_filter)

        return qs.order_by('-timestamp')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)

        def serialize_log(log):
            return {
                'id': log.id,
                'timestamp': log.timestamp,
                'user_name': log.actor.full_name if log.actor else 'System',
                'action': log.get_action_display(),
                'target': str(log.target) if log.target else None,
                'ip_address': log.metadata.get('ip_address') if isinstance(log.metadata, dict) else None,
                'details': log.metadata,
            }

        if page is not None:
            return paginator.get_paginated_response([serialize_log(l) for l in page])

        return Response([serialize_log(l) for l in queryset[:100]])
