from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
# Register with empty string since the prefix is already in config/urls.py
router.register(r'periods', views.ReportingPeriodViewSet, basename='period')
router.register(r'', views.ReportViewSet, basename='report')

urlpatterns = [
    path('', include(router.urls)),
    # Report actions
    path('<int:pk>/submit/', views.ReportViewSet.as_view({'post': 'submit'}), name='report-submit'),
    path('<int:pk>/mark-reviewed/', views.ReportViewSet.as_view({'post': 'mark_reviewed'}), name='report-mark-reviewed'),
    # Custom report list actions
    path('my-reports/', views.ReportViewSet.as_view({'get': 'my_reports'}), name='report-my-reports'),
    path('pending-approval/', views.ReportViewSet.as_view({'get': 'pending_approval'}), name='report-pending-approval'),
    path('team-reports/', views.ReportViewSet.as_view({'get': 'team_reports'}), name='report-team-reports'),
    path('all-reports/', views.ReportViewSet.as_view({'get': 'all_reports'}), name='report-all-reports'),
    path('dashboard-stats/', views.ReportViewSet.as_view({'get': 'dashboard_stats'}), name='report-dashboard-stats'),
    path('recent-activity/', views.ReportViewSet.as_view({'get': 'recent_activity'}), name='report-recent-activity'),
    # Comments
    path('comments/', views.CommentViewSet.as_view({'get': 'list', 'post': 'create'}), name='comment-list'),
    path('comments/<int:pk>/', views.CommentViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='comment-detail'),
]