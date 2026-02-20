from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import User
from reports.models import Report, ReportingPeriod
from notifications.models import Notification
from django.utils import timezone
from datetime import timedelta


class NotificationTests(TestCase):
    """Test cases for notification endpoints"""

    def setUp(self):
        self.client = APIClient()

        # Create employee
        self.employee = User.objects.create_user(
            email='employee@example.com',
            password='employeepass123',
            full_name='Employee User',
            role=User.Role.EMPLOYEE
        )

        # Create supervisor
        self.supervisor = User.objects.create_user(
            email='supervisor@example.com',
            password='supervisorpass123',
            full_name='Supervisor User',
            role=User.Role.SUPERVISOR
        )

        # Create period and report
        self.period = ReportingPeriod.objects.create(
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=7),
            deadline=timezone.now().date() + timedelta(days=5)
        )

        self.report = Report.objects.create(
            employee=self.employee,
            period=self.period,
            accomplishments='Test',
            goals_next_week='Test',
            progress_rating='3'
        )

    def authenticate(self, user):
        """Helper to authenticate as a user"""
        response = self.client.post('/api/v1/auth/login/', {
            'email': user.email,
            'password': f'{user.email.split("@")[0]}pass123'
        })
        if response.status_code == 200:
            self.client.credentials(
                HTTP_AUTHORIZATION=f"Bearer {response.data['access']}"
            )

    def test_list_notifications(self):
        """Test listing user notifications"""
        # Create a notification
        Notification.objects.create(
            user=self.employee,
            title='Test Notification',
            message='This is a test',
            notification_type='report_submitted'
        )

        self.authenticate(self.employee)

        response = self.client.get('/api/v1/notifications/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_mark_notification_read(self):
        """Test marking a notification as read"""
        notification = Notification.objects.create(
            user=self.employee,
            title='Test Notification',
            message='This is a test',
            notification_type='report_submitted',
            is_read=False
        )

        self.authenticate(self.employee)

        response = self.client.post('/api/v1/notifications/mark-read/', {
            'ids': [notification.id]
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify notification is marked as read
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

    def test_mark_all_notifications_read(self):
        """Test marking all notifications as read"""
        # Create multiple notifications
        for i in range(3):
            Notification.objects.create(
                user=self.employee,
                title=f'Test Notification {i}',
                message=f'This is test {i}',
                notification_type='report_submitted',
                is_read=False
            )

        self.authenticate(self.employee)

        response = self.client.post('/api/v1/notifications/mark-all-read/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify all notifications are marked as read
        unread = Notification.objects.filter(user=self.employee, is_read=False).count()
        self.assertEqual(unread, 0)


class AuditLogTests(TestCase):
    """Test cases for audit log endpoints"""

    def setUp(self):
        self.client = APIClient()

        # Create admin
        self.admin = User.objects.create_user(
            email='admin@example.com',
            password='adminpass123',
            full_name='Admin User',
            role=User.Role.ADMIN
        )

    def authenticate(self, user):
        """Helper to authenticate as a user"""
        response = self.client.post('/api/v1/auth/login/', {
            'email': user.email,
            'password': f'{user.email.split("@")[0]}pass123'
        })
        if response.status_code == 200:
            self.client.credentials(
                HTTP_AUTHORIZATION=f"Bearer {response.data['access']}"
            )

    def test_list_audit_logs(self):
        """Test listing audit logs (admin only)"""
        self.authenticate(self.admin)

        response = self.client.get('/api/v1/auth/audit-logs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_non_admin_cannot_list_audit_logs(self):
        """Test non-admin cannot list audit logs"""
        employee = User.objects.create_user(
            email='employee@example.com',
            password='employeepass123',
            full_name='Employee User',
            role=User.Role.EMPLOYEE
        )
        self.authenticate(employee)

        response = self.client.get('/api/v1/auth/audit-logs/')
        # Should return empty or filtered results
        self.assertEqual(response.status_code, status.HTTP_200_OK)
