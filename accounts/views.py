from rest_framework import viewsets, status
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
from rest_framework_simplejwt.exceptions import InvalidToken
import csv
import io

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
    page_size = 20
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
                'role': user.role
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
        serializer = UserProfileSerializer(
            request.user,
            data=request.data,
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

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreationSerializer
        return UserProfileSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.SUPERVISOR:
            # Supervisors see their employees (placeholder logic for team mapping)
            return User.objects.filter(role=User.Role.EMPLOYEE)
        elif user.role == User.Role.ADMIN:
            return User.objects.all()
        return User.objects.filter(id=user.id)

    def create(self, request, *args, **kwargs):
        """
        Create a new user (admin only)
        """
        if request.user.role != User.Role.ADMIN:
            return Response(
                {"error": "Only admins can create users"},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def employees(self, request):
        """Returns list of employees for assignment or viewing"""
        employees = User.objects.filter(role=User.Role.EMPLOYEE)
        serializer = self.get_serializer(employees, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='bulk-import')
    def bulk_import(self, request):
        """
        PRD section 5.4 - Admin Panel
        Bulk import users from CSV file
        Expected CSV columns: email, full_name, role, supervisor_email
        """
        if request.user.role != User.Role.ADMIN:
            return Response(
                {"error": "Only admins can bulk import users"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = BulkUserImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        csv_file = serializer.validated_data['csv_file']
        decoded = csv_file.read().decode('utf-8')
        reader = csv.DictReader(io.StringIO(decoded))

        success_count = 0
        errors = []
        default_password = "Gridlog2026!"  # Will require password reset

        for row_num, row in enumerate(reader, start=2):  # Start at 2 (1 is header)
            try:
                email = row.get('email', '').strip().lower()
                full_name = row.get('full_name', '').strip()
                role = row.get('role', 'employee').strip().lower()
                supervisor_email = row.get('supervisor_email', '').strip().lower()

                # Validate required fields
                if not email:
                    errors.append(f"Row {row_num}: Email is required")
                    continue

                if not full_name:
                    errors.append(f"Row {row_num}: Full name is required")
                    continue

                # Validate role
                if role not in ['employee', 'supervisor', 'admin']:
                    errors.append(f"Row {row_num}: Invalid role '{role}'")
                    continue

                # Check if user already exists
                if User.objects.filter(email=email).exists():
                    errors.append(f"Row {row_num}: User with email '{email}' already exists")
                    continue

                # Create user
                user = User.objects.create_user(
                    email=email,
                    full_name=full_name,
                    role=role,
                    password=default_password,
                    password_reset_required=True
                )

                # Assign supervisor if provided
                if supervisor_email and role == 'employee':
                    try:
                        supervisor = User.objects.get(email=supervisor_email, role=User.Role.SUPERVISOR)
                        user.supervisor = supervisor
                        user.save()
                    except User.DoesNotExist:
                        errors.append(f"Row {row_num}: Supervisor '{supervisor_email}' not found")

                # Log user creation
                AuditLog.log(
                    actor=request.user,
                    action=AuditLog.Action.USER_CREATE,
                    target=user,
                    metadata={"message": f"Bulk imported user {email}"}
                )

                success_count += 1

            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")

        return Response({
            "success_count": success_count,
            "error_count": len(errors),
            "errors": errors,
            "message": f"Successfully imported {success_count} users. {len(errors)} errors."
        })


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
            return AuditLog.objects.all().order_by('-timestamp')
        elif user.role == User.Role.SUPERVISOR:
            # Supervisors see logs for reports/comments in their scope
            return AuditLog.objects.filter(
                actor__role=User.Role.EMPLOYEE
            ).order_by('-timestamp')
        return AuditLog.objects.filter(actor=user).order_by('-timestamp')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)

        if page is not None:
            data = [{
                'id': log.id,
                'timestamp': log.timestamp,
                'actor': log.actor.full_name,
                'action': log.get_action_display(),
                'metadata': log.metadata
            } for log in page]
            return paginator.get_paginated_response(data)

        # Fallback for no pagination
        data = [{
            'id': log.id,
            'timestamp': log.timestamp,
            'actor': log.actor.full_name,
            'action': log.get_action_display(),
            'metadata': log.metadata
        } for log in queryset[:100]]
        return Response(data)
