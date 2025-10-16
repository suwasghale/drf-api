from rest_framework import serializers
from apps.notifications.models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id", "user", "title", "message", "notification_type",
            "level", "is_read", "read_at", "created_at", "updated_at"
        ]
        read_only_fields = ["user", "created_at", "updated_at", "read_at"]
