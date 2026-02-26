from rest_framework import viewsets, status, permissions, serializers
import csv
import io
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone
from datetime import timedelta, datetime
from .models import ReportingPeriod, Report, Comment
from .serializers import (
    ReportingPeriodSerializer,
    ReportSerializer,
    ReportDetailSerializer,
    CommentSerializer
)
from accounts.models import User, AuditLog
from django.http import HttpResponse
from django.db.models import Count, Q
from django.db import transaction
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
import io


class ReportPagination(PageNumberPagination):
    """Pagination for report list endpoints"""
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100

class IsEmployee(permissions.BasePermission):
    """Custom permission for employee-only access"""
    def has_permission(self, request, view):
        return request.user.role == User.Role.EMPLOYEE

class IsSupervisor(permissions.BasePermission):
    """Custom permission for supervisor-only access"""
    def has_permission(self, request, view):
        return request.user.role == User.Role.SUPERVISOR

class ReportingPeriodViewSet(viewsets.ModelViewSet):
    """
    PRD section 6.3 - Reporting Period Rules
    Handles management of reporting periods
    """
    queryset = ReportingPeriod.objects.all()
    serializer_class = ReportingPeriodSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Employees and supervisors only see active periods by default
        if self.request.user.role in [User.Role.EMPLOYEE, User.Role.SUPERVISOR]:
            return ReportingPeriod.objects.filter(is_closed=False)
        return super().get_queryset()

    @action(detail=True, methods=['post'], url_path='close')
    def close_period(self, request, pk=None):
        """Transition the period to closed status"""
        if request.user.role != User.Role.ADMIN:
            return Response({"error": "Only admins can close reporting periods"}, status=status.HTTP_403_FORBIDDEN)
        
        period = self.get_object()
        
        with transaction.atomic():
            period = ReportingPeriod.objects.select_for_update().get(pk=period.pk)
            period.is_closed = True
            period.save()
            
            # Log the action
            AuditLog.log(
                actor=request.user,
                action=AuditLog.Action.PERIOD_CLOSE,
                metadata={"message": f"Closed reporting period {period}", "period_id": period.id}
            )
        
        return Response(ReportingPeriodSerializer(period).data)

    @action(detail=True, methods=['post'], url_path='reopen')
    def reopen_period(self, request, pk=None):
        """Reopen a closed reporting period"""
        if request.user.role != User.Role.ADMIN:
            return Response({"error": "Only admins can reopen reporting periods"}, status=status.HTTP_403_FORBIDDEN)

        period = self.get_object()

        with transaction.atomic():
            period = ReportingPeriod.objects.select_for_update().get(pk=period.pk)
            period.is_closed = False
            period.save()

            # Log the action
            AuditLog.log(
                actor=request.user,
                action=AuditLog.Action.PERIOD_REOPEN,
                metadata={"message": f"Reopened reporting period {period}", "period_id": period.id}
            )

        return Response(ReportingPeriodSerializer(period).data)

class ReportViewSet(viewsets.ModelViewSet):
    """
    PRD section 5.2 - Employee Portal & section 5.3 - Supervisor Dashboard
    Handles report creation, retrieval, and submission
    """
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = ReportPagination
    
    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.EMPLOYEE:
            qs = Report.objects.filter(employee=user)
        elif user.role == User.Role.SUPERVISOR:
            qs = Report.objects.filter(employee__supervisor=user)
        else:
            qs = Report.objects.all()

        # Add filters for Phase 3
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        employee_search = self.request.query_params.get('employee')

        if start_date:
            qs = qs.filter(period__start_date__gte=start_date)
        if end_date:
            qs = qs.filter(period__end_date__lte=end_date)
        if employee_search:
            if employee_search.isdigit():
                qs = qs.filter(employee_id=employee_search)
            else:
                qs = qs.filter(employee__full_name__icontains=employee_search)

        return qs.select_related('period', 'employee').order_by('-period__start_date')
    
    def get_serializer_class(self):
        if self.action in ['retrieve', 'update', 'partial_update']:
            return ReportDetailSerializer
        return super().get_serializer_class()

    def create(self, request, *args, **kwargs):
        """Only employees can create reports"""
        if request.user.role != User.Role.EMPLOYEE:
            return Response(
                {"error": "Only employees can create reports"},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """Only employees can update their own draft reports"""
        if request.user.role != User.Role.EMPLOYEE:
            return Response(
                {"error": "Only employees can update reports"},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Only employees can delete their own draft reports"""
        if request.user.role != User.Role.EMPLOYEE:
            return Response(
                {"error": "Only employees can delete reports"},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)

    def perform_create(self, serializer):
        # Ensure employee can only create report for current period
        current_period = ReportingPeriod.objects.filter(is_closed=False).first()
        if not current_period:
            raise serializers.ValidationError("No active reporting period available")
        
        # Check if report already exists for this period
        if Report.objects.filter(employee=self.request.user, period=current_period).exists():
            raise serializers.ValidationError("Report already exists for this period")
        
        serializer.save(employee=self.request.user, period=current_period)
    
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """
        PRD section 6.2 - Report Status Lifecycle
        Transition a draft report to Submitted status
        """
        report = self.get_object()
        
        with transaction.atomic():
            # Use select_for_update to handle concurrency
            report = Report.objects.select_for_update().get(pk=report.pk)
            
            # Validate report can be submitted
            if report.employee != request.user:
                return Response(
                    {"error": "You can only submit your own reports"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            if report.status not in [Report.Status.NOT_STARTED, Report.Status.DRAFT]:
                return Response(
                    {"error": "Only draft or not started reports can be submitted"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate required fields
            if not report.accomplishments or not report.goals_next_week or not report.progress_rating:
                return Response(
                    {"error": "Accomplishments, goals_next_week, and progress_rating are required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Submit the report
            report.status = Report.Status.SUBMITTED
            report.submitted_at = timezone.now()
            report.save()
            
            # Log the submission in audit log
            AuditLog.log(
                actor=request.user,
                action=AuditLog.Action.REPORT_SUBMIT,
                target=report,
                metadata={"message": "Report submitted to supervisor"}
            )
            
            # Send notification to supervisor after transaction commits
            from notifications.tasks import send_report_submitted_notification
            transaction.on_commit(lambda: send_report_submitted_notification.delay(report.id))
        
        return Response(ReportDetailSerializer(report).data)
    
    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        """
        PRD section 5.3 - Supervisor Dashboard & section 6.2 - Report Status Lifecycle
        Transition a report to Reviewed status
        """
        # PRD section 5.3 - Strictly Supervisor only for review
        if request.user.role != User.Role.SUPERVISOR:
            return Response(
                {"error": "Only supervisors can review reports. Admins manage the platform only."},
                status=status.HTTP_403_FORBIDDEN
            )

        report = self.get_object()

        with transaction.atomic():
            # Use select_for_update to handle concurrency
            report = Report.objects.select_for_update().get(pk=report.pk)

            if report.status != Report.Status.SUBMITTED:
                return Response(
                    {"error": "Only submitted reports can be reviewed"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Verify supervisor is assigned to this employee
            if report.employee.supervisor != request.user:
                return Response(
                    {"error": "You can only review reports from your team members"},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Mark as reviewed
            report.status = Report.Status.REVIEWED
            report.reviewed_at = timezone.now()
            report.save()

            # Log the review in audit log
            AuditLog.log(
                actor=request.user,
                action=AuditLog.Action.REPORT_REVIEW,
                target=report,
                metadata={"message": "Report marked as reviewed"}
            )

            # Send notification to employee after transaction commits
            from notifications.tasks import send_report_reviewed_notification
            transaction.on_commit(lambda: send_report_reviewed_notification.delay(report.id))

        return Response(ReportDetailSerializer(report).data)

    @action(detail=True, methods=['post'], url_path='request-revision')
    def request_revision(self, request, pk=None):
        """
        New workflow enhancement: Request changes from employee.
        Transitions report to REVISION_REQUESTED status.
        """
        if request.user.role != User.Role.SUPERVISOR:
            return Response(
                {"error": "Only supervisors can request revisions"},
                status=status.HTTP_403_FORBIDDEN
            )

        report = self.get_object()

        if report.status != Report.Status.SUBMITTED:
            return Response(
                {"error": "Can only request revision for submitted reports"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if report.employee.supervisor != request.user:
            return Response(
                {"error": "You can only request revisions for your team members"},
                status=status.HTTP_403_FORBIDDEN
            )

        comment_body = request.data.get('comment', 'Supervisor requested a revision.')

        with transaction.atomic():
            # Transition status
            report.status = Report.Status.REVISION_REQUESTED
            report.save()

            # Create a comment automatically
            from .models import Comment
            Comment.objects.create(
                report=report,
                author=request.user,
                body=f"[SYSTEM: Revision Requested] {comment_body}"
            )

            # Log in audit trail
            AuditLog.log(
                actor=request.user,
                action=AuditLog.Action.REPORT_REVISION_REQUESTED,
                target=report,
                metadata={"message": "Supervisor requested a revision", "comment": comment_body}
            )

            # Notification logic (placeholder for task implementation)
            # from notifications.tasks import send_revision_requested_notification
            # transaction.on_commit(lambda: send_revision_requested_notification.delay(report.id))

        return Response(ReportDetailSerializer(report).data)

    @action(detail=True, methods=['post'], url_path='reset-to-draft')
    def reset_to_draft(self, request, pk=None):
        """
        PRD section 6.2 - Admin-only: reset a report back to Draft status
        in exceptional circumstances.
        """
        if request.user.role != User.Role.ADMIN:
            return Response(
                {"error": "Only admins can reset reports to draft"},
                status=status.HTTP_403_FORBIDDEN
            )

        report = self.get_object()

        if report.status == Report.Status.DRAFT:
            return Response(
                {"error": "Report is already in Draft status"},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            report = Report.objects.select_for_update().get(pk=report.pk)
            report.status = Report.Status.DRAFT
            report.submitted_at = None
            report.reviewed_at = None
            report.save()

            AuditLog.log(
                actor=request.user,
                action=AuditLog.Action.REPORT_UPDATE,
                target=report,
                metadata={"message": "Admin reset report to Draft status"}
            )

        return Response(ReportDetailSerializer(report).data)

    @action(detail=False, methods=['get'], url_path='dashboard-stats')
    def dashboard_stats(self, request):
        """Returns counts for reports by status for the current user's scope"""
        queryset = self.get_queryset()
        
        # Determine what "myReports" (or "Team Reports") should count
        if request.user.role == User.Role.EMPLOYEE:
            my_reports_count = queryset.filter(employee=request.user).count()
        else:
            # For supervisors, this represents their entire team's reports
            my_reports_count = queryset.count()
            
        stats = {
            'myReports': my_reports_count,
            'pendingReview': queryset.filter(status=Report.Status.SUBMITTED).count(),
            'reviewed': queryset.filter(status=Report.Status.REVIEWED).count(),
            'draft': queryset.filter(status=Report.Status.DRAFT).count()
        }
        return Response(stats)

    @action(detail=False, methods=['get'], url_path='recent-activity')
    def recent_activity(self, request):
        """Returns the last 10 audit logs relevant to the user"""
        logs = AuditLog.objects.filter(
            target_model='report'
        ).order_by('-timestamp')[:10]
        
        activity = []
        for log in logs:
            activity.append({
                'id': log.target_id,  # Use report ID for navigation, not audit log ID
                'log_id': log.id,
                'title': log.get_action_display(),
                'date': log.timestamp,
                'message': log.metadata.get('message', '') if log.metadata else '',
                'actor': log.actor.full_name if log.actor else 'System'
            })
        return Response(activity)

    @action(detail=False, methods=['get'], url_path='my-reports')
    def my_reports(self, request):
        reports = self.get_queryset().filter(employee=request.user)
        return Response(self.get_serializer(reports, many=True).data)

    @action(detail=False, methods=['get'], url_path='pending-approval')
    def pending_approval(self, request):
        reports = self.get_queryset().filter(
            status=Report.Status.SUBMITTED
        ).select_related('period', 'employee')
        return Response(self.get_serializer(reports, many=True).data)

    @action(detail=False, methods=['get'], url_path='team-reports')
    def team_reports(self, request):
        if request.user.role != User.Role.SUPERVISOR:
            return Response({"error": "Only supervisors can view team reports"}, status=status.HTTP_403_FORBIDDEN)
        reports = self.get_queryset()
        return Response(self.get_serializer(reports, many=True).data)

    @action(detail=False, methods=['get'], url_path='team-oversight')
    def team_oversight(self, request):
        """
        PRD feature - Custom Team Oversight metrics for Supervisors.
        Calculates report statistics per team member.
        """
        if request.user.role != User.Role.SUPERVISOR:
            return Response({"error": "Only supervisors can view team oversight metrics"}, status=status.HTTP_403_FORBIDDEN)

        current_period = ReportingPeriod.objects.filter(is_closed=False).first()
        team_members = User.objects.filter(role=User.Role.EMPLOYEE, supervisor=request.user)
        
        member_stats = []
        for member in team_members:
            # Query all reports for this member
            member_reports = Report.objects.filter(employee=member)
            
            # Extract basic metrics
            total_reports = member_reports.count()
            pending_review = member_reports.filter(status=Report.Status.SUBMITTED).count()
            reviewed = member_reports.filter(status=Report.Status.REVIEWED).count()

            # Determine current period status
            current_status = 'Not Started'
            if current_period:
                current_report = member_reports.filter(period=current_period).first()
                if current_report:
                    current_status = current_report.get_status_display()

            member_stats.append({
                'id': member.id,
                'name': member.full_name,
                'email': member.email,
                'total_reports': total_reports,
                'pending_review': pending_review,
                'reviewed': reviewed,
                'current_status': current_status
            })

        return Response({
            'total_members': team_members.count(),
            'members': member_stats
        })

    @action(detail=False, methods=['get'], url_path='all-reports')
    def all_reports(self, request):
        """Returns all reports (admin only)"""
        if request.user.role != User.Role.ADMIN:
            return Response({"error": "Only admins can view all reports"}, status=status.HTTP_403_FORBIDDEN)
        reports = Report.objects.all().select_related('period', 'employee')
        return Response(self.get_serializer(reports, many=True).data)

    @action(detail=False, methods=['get'], url_path='export-pdf')
    def export_pdf(self, request):
        """
        PRD section 5.4 - Admin Panel
        Export reports as PDF, filterable by date range, team, or org-wide
        """
        if request.user.role != User.Role.ADMIN:
            return Response({"error": "Only admins can export reports"}, status=status.HTTP_403_FORBIDDEN)

        # Get filter parameters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        supervisor_id = request.query_params.get('supervisor_id')

        # Build queryset
        queryset = Report.objects.select_related('period', 'employee', 'employee__supervisor').order_by('-period__start_date', 'employee__full_name')

        if start_date:
            queryset = queryset.filter(period__start_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(period__end_date__lte=end_date)
        if supervisor_id:
            queryset = queryset.filter(employee__supervisor_id=supervisor_id)

        # Generate PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        elements = []
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=18, spaceAfter=20)
        heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'], fontSize=12, spaceBefore=15, spaceAfter=10)
        normal_style = styles['Normal']

        # Title
        elements.append(Paragraph("Gridlog Weekly Reports Export", title_style))
        elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", normal_style))
        elements.append(Spacer(1, 20))

        # Filter info
        filter_info = []
        if start_date:
            filter_info.append(f"From: {start_date}")
        if end_date:
            filter_info.append(f"To: {end_date}")
        if filter_info:
            elements.append(Paragraph(f"Filters: {', '.join(filter_info)}", normal_style))
            elements.append(Spacer(1, 10))

        elements.append(Paragraph(f"Total Reports: {queryset.count()}", normal_style))
        elements.append(Spacer(1, 20))

        # Table data
        table_data = [['Employee', 'Period', 'Status', 'Rating', 'Submitted']]

        for report in queryset[:500]:  # Limit to 500 for performance
            period_str = f"{report.period.start_date} - {report.period.end_date}"
            status_str = report.get_status_display()
            rating_str = report.get_progress_rating_display() or 'N/A'
            submitted_str = report.submitted_at.strftime('%Y-%m-%d %H:%M') if report.submitted_at else 'Not submitted'

            table_data.append([
                report.employee.full_name,
                period_str,
                status_str,
                rating_str,
                submitted_str
            ])

        # Create table
        table = Table(table_data, colWidths=[2*inch, 1.5*inch, 1*inch, 1*inch, 1.2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ]))

        elements.append(table)
        doc.build(elements)

        # Return PDF response
        buffer.seek(0)
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="gridlog_reports_{datetime.now().strftime("%Y%m%d")}.pdf"'
        return response

    @action(detail=False, methods=['get'], url_path='export-csv')
    def export_csv(self, request):
        """
        PRD section 5.4 - Admin Panel
        Export reports as CSV, filterable by date range, team, or org-wide
        """
        if request.user.role != User.Role.ADMIN:
            return Response({"error": "Only admins can export reports"}, status=status.HTTP_403_FORBIDDEN)

        # Get filter parameters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        supervisor_id = request.query_params.get('supervisor_id')

        # Build queryset
        queryset = Report.objects.select_related('period', 'employee').order_by('-period__start_date', 'employee__full_name')

        if start_date:
            queryset = queryset.filter(period__start_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(period__end_date__lte=end_date)
        if supervisor_id:
            queryset = queryset.filter(employee__supervisor_id=supervisor_id)

        # Generate CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Employee', 'Email', 'Reporting Period', 'Status', 'Rating', 'Submitted At', 'Accomplishments', 'Goals Next Week', 'Blockers'])

        for report in queryset[:1000]:  # Limit for stability
            writer.writerow([
                report.employee.full_name,
                report.employee.email,
                f"{report.period.start_date} to {report.period.end_date}",
                report.get_status_display(),
                report.get_progress_rating_display() or 'N/A',
                report.submitted_at.strftime('%Y-%m-%d %H:%M') if report.submitted_at else 'N/A',
                report.accomplishments[:100] + '...' if len(report.accomplishments) > 100 else report.accomplishments,
                report.goals_next_week[:100] + '...' if len(report.goals_next_week) > 100 else report.goals_next_week,
                report.blockers[:100] + '...' if len(report.blockers) > 100 else report.blockers
            ])

        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="gridlog_reports_{datetime.now().strftime("%Y%m%d")}.csv"'
        return response

    @action(detail=False, methods=['get'], url_path='organization-stats')
    def organization_stats(self, request):
        """
        PRD section 5.4 - Admin Panel
        Returns org-wide submission rates and metrics
        """
        if request.user.role != User.Role.ADMIN:
            return Response({"error": "Only admins can view organization stats"}, status=status.HTTP_403_FORBIDDEN)

        current_period = ReportingPeriod.objects.filter(is_closed=False).first()
        if not current_period:
            return Response({"error": "No active reporting period"}, status=status.HTTP_404_NOT_FOUND)

        total_employees = User.objects.filter(role=User.Role.EMPLOYEE, is_active=True).count()
        submitted_count = Report.objects.filter(period=current_period, status__in=[Report.Status.SUBMITTED, Report.Status.REVIEWED]).count()
        draft_count = Report.objects.filter(period=current_period, status=Report.Status.DRAFT).count()
        not_started_count = total_employees - (submitted_count + draft_count)

        submission_rate = (submitted_count / total_employees * 100) if total_employees > 0 else 0

        # Weekly trend for last 4 periods
        trend = []
        last_4_periods = ReportingPeriod.objects.all().order_by('-start_date')[:4]
        for p in reversed(last_4_periods):
            p_submitted = Report.objects.filter(period=p, status__in=[Report.Status.SUBMITTED, Report.Status.REVIEWED]).count()
            p_rate = (p_submitted / total_employees * 100) if total_employees > 0 else 0
            trend.append({
                'period': str(p),
                'rate': round(p_rate, 1)
            })

        return Response({
            'totalEmployees': total_employees,
            'submittedCount': submitted_count,
            'submissionRate': round(submission_rate, 2),
            'draftCount': draft_count,
            'notStartedCount': max(0, not_started_count),
            'trend': trend,
            'period': str(current_period)
        })
    


class CommentViewSet(viewsets.ModelViewSet):
    """
    PRD section 7 - Notification System and section 9.3 - Key API Endpoints
    Handles comment creation, retrieval, and one-level reply threading
    """
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.EMPLOYEE:
            # Employees can see comments on their own reports
            return Comment.objects.filter(report__employee=user).select_related('author', 'report')
        elif user.role == User.Role.SUPERVISOR:
            # Supervisors can see comments on reports from their team members
            return Comment.objects.filter(
                report__employee__supervisor=user
            ).select_related('author', 'report')
        return Comment.objects.all().select_related('author', 'report')
    
    def perform_create(self, serializer):
        report_id = self.request.data.get('report')
        try:
            report = Report.objects.get(id=report_id)
        except Report.DoesNotExist:
            raise serializers.ValidationError({"report": "Report not found"})
        
        # Check if user can comment on this report
        if self.request.user.role == User.Role.EMPLOYEE:
            if report.employee != self.request.user:
                raise permissions.PermissionDenied("You can only comment on your own reports")
        elif self.request.user.role == User.Role.SUPERVISOR:
            if report.employee.supervisor != self.request.user:
                raise permissions.PermissionDenied("You can only comment on reports from your team members")
        
        # Check parent comment if provided
        parent_id = self.request.data.get('parent')
        if parent_id:
            try:
                parent = Comment.objects.get(id=parent_id)
                # PRD section 13: One-level threading only
                if parent.parent:
                    raise serializers.ValidationError({"parent": "Reply threading beyond one level is not supported in v1"})
            except Comment.DoesNotExist:
                raise serializers.ValidationError({"parent": "Parent comment not found"})
        
        with transaction.atomic():
            serializer.save(author=self.request.user)
            comment = serializer.instance
            
            # Log the comment in audit log
            AuditLog.log(
                actor=self.request.user,
                action=AuditLog.Action.COMMENT_ADD,
                target=report,
                metadata={
                    "message": "Comment added to report",
                    "comment_id": str(comment.id)
                }
            )
            
            # Trigger notification after transaction commits
            from notifications.tasks import send_comment_notification
            transaction.on_commit(lambda: send_comment_notification.delay(comment.id))
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)