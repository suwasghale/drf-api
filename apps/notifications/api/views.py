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


