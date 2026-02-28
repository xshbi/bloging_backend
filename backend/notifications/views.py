from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(generics.ListAPIView):
    """Get all notifications for logged in user"""
    serializer_class   = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Notification.objects.filter(
            recipient=self.request.user
        ).select_related('sender', 'post', 'comment').order_by('-created_at')

        # filter unread only if requested
        unread_only = self.request.query_params.get('unread')
        if unread_only == 'true':
            queryset = queryset.filter(is_read=False)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'count'        : queryset.count(),
            'unread_count' : queryset.filter(is_read=False).count(),
            'results'      : serializer.data
        })


class MarkNotificationReadView(APIView):
    """Mark a single notification as read"""
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        try:
            notification = Notification.objects.get(pk=pk, recipient=request.user)
            notification.is_read = True
            notification.save(update_fields=['is_read'])
            return Response({'message': 'Marked as read.'})
        except Notification.DoesNotExist:
            return Response(
                {'error': 'Notification not found.'},
                status=status.HTTP_404_NOT_FOUND
            )


class MarkAllReadView(APIView):
    """Mark all notifications as read"""
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        updated = Notification.objects.filter(
            recipient=request.user,
            is_read  =False
        ).update(is_read=True)
        return Response({'message': f'{updated} notifications marked as read.'})


class ClearAllNotificationsView(APIView):
    """Delete all notifications for logged in user"""
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        deleted, _ = Notification.objects.filter(recipient=request.user).delete()
        return Response(
            {'message': f'{deleted} notifications cleared.'},
            status=status.HTTP_204_NO_CONTENT
        )


class UnreadCountView(APIView):
    """Quick endpoint just for the notification bell count"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(
            recipient=request.user,
            is_read  =False
        ).count()
        return Response({'unread_count': count})