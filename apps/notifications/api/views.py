from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone

from apps.notifications.models import Notification
from apps.notifications.api.serializers import NotificationSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    """
    Handles CRUD for user notifications.
    Authenticated users can only access their own notifications.
    Admins can view all.
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Notification.objects.all()
        return user.notifications.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["post"], url_path="mark-all-read")
    def mark_all_read(self, request):
        """Mark all user notifications as read."""
        count = request.user.notifications.filter(is_read=False).update(
            is_read=True, read_at=timezone.now()
        )
        return Response({"updated": count}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="mark-read")
    def mark_read(self, request, id=None):
        """Mark a single notification as read."""
        notification = self.get_object()
        notification.mark_as_read()
        return Response({"detail": "Marked as read."}, status=status.HTTP_200_OK)
