from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from .models import Notification
from .serializers import NotificationSerializer

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    PRD section 7 - Notification System and section 9.3 - Key API Endpoints
    Handles in-app notification retrieval and management
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    ordering = ['-created_at']
    
    def get_queryset(self):
        # Return only notifications for the current user
        return Notification.objects.filter(recipient=self.request.user)
    
    @action(detail=False, methods=['post'])
    def read(self, request):
        """
        PRD section 9.3 - Key API Endpoints
        Marks one or multiple notifications as read
        """
        notification_ids = request.data.get('ids', [])
        
        if not notification_ids:
            return Response(
                {"error": "Notification IDs are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update only the notifications belonging to the current user
        updated = Notification.objects.filter(
            id__in=notification_ids,
            recipient=request.user
        ).update(is_read=True)
        
        return Response({"updated": updated})
    
    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_read(self, request):
        """
        Marks all notifications for the current user as read
        """
        updated = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).update(is_read=True)
        
        return Response({"updated": updated})
    
    @action(detail=False, methods=['get'], url_path='unread-count')
    def unread_count(self, request):
        """
        Returns the count of unread notifications for the current user
        """
        count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
        
        return Response({"unread_count": count})