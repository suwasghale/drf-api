from rest_framework import serializers
from apps.support.models import Ticket, TicketMessage, MessageAttachment
from django.contrib.auth import get_user_model

User = get_user_model()

class MessageAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageAttachment
        fields = ["id", "file", "file_name", "content_type", "size", "created_at"]
        read_only_fields = ["id", "file_name", "content_type", "size", "created_at"]


class TicketMessageSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username", read_only=True)
    attachments = MessageAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = TicketMessage
        fields = ["id", "ticket", "user", "body", "is_internal", "is_from_customer", "created_at", "attachments"]
        read_only_fields = ["id", "ticket", "user", "created_at", "is_from_customer"]


class TicketCreateSerializer(serializers.ModelSerializer):
    """
    Input serializer for creating tickets. Creator is assigned from request.user.
    """
    class Meta:
        model = Ticket
        fields = ["title", "description", "order", "priority", "tags", "is_public"]

    def create(self, validated_data):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        ticket = Ticket.objects.create(creator=user, **validated_data)
        return ticket

class TicketSerializer(serializers.ModelSerializer):
    creator = serializers.CharField(source="creator.username", read_only=True)
    assigned_to = serializers.CharField(source="assigned_to.username", read_only=True)
    messages = TicketMessageSerializer(many=True, read_only=True)

    class Meta:
        model = Ticket
        fields = [
            "id", "reference", "title", "description", "creator", "assigned_to",
            "order", "status", "priority", "is_public", "tags",
            "created_at", "updated_at", "last_activity_at", "sla_due_at", "messages"
        ]
        read_only_fields = ["id", "reference", "creator", "created_at", "updated_at", "last_activity_at"]
