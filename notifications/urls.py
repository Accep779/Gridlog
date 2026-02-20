# notifications/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
# Register with empty string since the prefix is already in config/urls.py
router.register(r'', views.NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
    path('mark-read/', views.NotificationViewSet.as_view({'post': 'read'}), name='notification-mark-read'),
    path('mark-all-read/', views.NotificationViewSet.as_view({'post': 'mark_all_read'}), name='notification-mark-all-read'),
    path('unread-count/', views.NotificationViewSet.as_view({'get': 'unread_count'}), name='notification-unread-count'),
]