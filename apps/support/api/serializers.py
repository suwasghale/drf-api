from rest_framework import serializers
from apps.support.models import Ticket, TicketMessage, MessageAttachment
from django.contrib.auth import get_user_model

User = get_user_model()

class MessageAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageAttachment
        fields = ["id", "file", "file_name", "content_type", "size", "created_at"]
        read_only_fields = ["id", "file_name", "content_type", "size", "created_at"]
