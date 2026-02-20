from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import User
from reports.models import Report, ReportingPeriod
from django.utils import timezone
from datetime import timedelta


class ReportTests(TestCase):
    """Test cases for report endpoints"""

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

        # Create admin
        self.admin = User.objects.create_user(
            email='admin@example.com',
            password='adminpass123',
            full_name='Admin User',
            role=User.Role.ADMIN
        )

        # Create active reporting period
        self.period = ReportingPeriod.objects.create(
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=7),
            deadline=timezone.now().date() + timedelta(days=5)
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

    def test_employee_can_create_report(self):
        """Test employee can create a new report"""
        self.authenticate(self.employee)

        response = self.client.post('/api/v1/reports/', {
            'accomplishments': 'Completed task A',
            'goals_next_week': 'Work on task B',
            'progress_rating': '3'
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'draft')

    def test_supervisor_cannot_create_report(self):
        """Test supervisor cannot create a report"""
        self.authenticate(self.supervisor)

        response = self.client.post('/api/v1/reports/', {
            'accomplishments': 'Completed task A',
            'goals_next_week': 'Work on task B',
            'progress_rating': '3'
        })

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_reports(self):
        """Test listing reports"""
        # Create a report first
        report = Report.objects.create(
            employee=self.employee,
            period=self.period,
            accomplishments='Test',
            goals_next_week='Test',
            progress_rating='3'
        )

        self.authenticate(self.employee)

        response = self.client.get('/api/v1/reports/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_report_detail(self):
        """Test getting report detail"""
        report = Report.objects.create(
            employee=self.employee,
            period=self.period,
            accomplishments='Test',
            goals_next_week='Test',
            progress_rating='3'
        )

        self.authenticate(self.employee)

        response = self.client.get(f'/api/v1/reports/{report.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['accomplishments'], 'Test')

    def test_submit_report(self):
        """Test submitting a report"""
        report = Report.objects.create(
            employee=self.employee,
            period=self.period,
            accomplishments='Completed task A',
            goals_next_week='Work on task B',
            progress_rating='3'
        )

        self.authenticate(self.employee)

        response = self.client.post(f'/api/v1/reports/{report.id}/submit/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'submitted')

    def test_submit_invalid_report(self):
        """Test submitting an incomplete report fails"""
        report = Report.objects.create(
            employee=self.employee,
            period=self.period,
            accomplishments='',  # Empty - should fail
            goals_next_week='Work on task B',
            progress_rating='3'
        )

        self.authenticate(self.employee)

        response = self.client.post(f'/api/v1/reports/{report.id}/submit/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_supervisor_can_approve_report(self):
        """Test supervisor can approve a submitted report"""
        report = Report.objects.create(
            employee=self.employee,
            period=self.period,
            accomplishments='Completed task A',
            goals_next_week='Work on task B',
            progress_rating='3',
            status=Report.Status.SUBMITTED
        )

        self.authenticate(self.supervisor)

        response = self.client.post(f'/api/v1/reports/{report.id}/approve/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'approved')

    def test_supervisor_can_reject_report(self):
        """Test supervisor can reject a submitted report"""
        report = Report.objects.create(
            employee=self.employee,
            period=self.period,
            accomplishments='Completed task A',
            goals_next_week='Work on task B',
            progress_rating='3',
            status=Report.Status.SUBMITTED
        )

        self.authenticate(self.supervisor)

        response = self.client.post(
            f'/api/v1/reports/{report.id}/reject/',
            {'feedback': 'Please revise the accomplishments section with more detail.'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'rejected')

    def test_reject_without_feedback_fails(self):
        """Test rejecting without feedback fails"""
        report = Report.objects.create(
            employee=self.employee,
            period=self.period,
            accomplishments='Completed task A',
            goals_next_week='Work on task B',
            progress_rating='3',
            status=Report.Status.SUBMITTED
        )

        self.authenticate(self.supervisor)

        response = self.client.post(
            f'/api/v1/reports/{report.id}/reject/',
            {'feedback': ''}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reject_with_short_feedback_fails(self):
        """Test rejecting with too short feedback fails"""
        report = Report.objects.create(
            employee=self.employee,
            period=self.period,
            accomplishments='Completed task A',
            goals_next_week='Work on task B',
            progress_rating='3',
            status=Report.Status.SUBMITTED
        )

        self.authenticate(self.supervisor)

        response = self.client.post(
            f'/api/v1/reports/{report.id}/reject/',
            {'feedback': 'Short'}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_dashboard_stats(self):
        """Test dashboard stats endpoint"""
        # Create some reports
        Report.objects.create(
            employee=self.employee,
            period=self.period,
            accomplishments='Test',
            goals_next_week='Test',
            progress_rating='3',
            status=Report.Status.DRAFT
        )
        Report.objects.create(
            employee=self.employee,
            period=self.period,
            accomplishments='Test',
            goals_next_week='Test',
            progress_rating='3',
            status=Report.Status.SUBMITTED
        )

        self.authenticate(self.employee)

        response = self.client.get('/api/v1/reports/dashboard-stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('myReports', response.data)
        self.assertIn('pendingReview', response.data)


class ReportingPeriodTests(TestCase):
    """Test cases for reporting period endpoints"""

    def setUp(self):
        self.client = APIClient()

        # Create admin
        self.admin = User.objects.create_user(
            email='admin@example.com',
            password='adminpass123',
            full_name='Admin User',
            role=User.Role.ADMIN
        )

        # Create employee
        self.employee = User.objects.create_user(
            email='employee@example.com',
            password='employeepass123',
            full_name='Employee User',
            role=User.Role.EMPLOYEE
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

    def test_list_periods(self):
        """Test listing reporting periods"""
        # Create periods
        ReportingPeriod.objects.create(
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=7),
            deadline=timezone.now().date() + timedelta(days=5)
        )

        self.authenticate(self.employee)

        response = self.client.get('/api/v1/reports/periods/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_can_create_period(self):
        """Test admin can create a reporting period"""
        self.authenticate(self.admin)

        response = self.client.post('/api/v1/reports/periods/', {
            'start_date': '2024-01-01',
            'end_date': '2024-01-07',
            'deadline': '2024-01-05'
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class CommentTests(TestCase):
    """Test cases for comment endpoints"""

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

    def test_employee_can_comment_on_own_report(self):
        """Test employee can add comment to their own report"""
        self.authenticate(self.employee)

        response = self.client.post('/api/v1/reports/comments/', {
            'report': self.report.id,
            'body': 'This is a comment'
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_supervisor_can_comment_on_employee_report(self):
        """Test supervisor can comment on employee report"""
        self.authenticate(self.supervisor)

        response = self.client.post('/api/v1/reports/comments/', {
            'report': self.report.id,
            'body': 'This is feedback from supervisor'
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_list_comments(self):
        """Test listing comments for a report"""
        # Create a comment first
        from reports.models import Comment
        Comment.objects.create(
            report=self.report,
            author=self.employee,
            body='Test comment'
        )

        self.authenticate(self.employee)

        response = self.client.get('/api/v1/reports/comments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
