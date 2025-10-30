from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction

from apps.support.models import Ticket, TicketMessage, MessageAttachment
from apps.support.api.serializers import TicketSerializer, TicketCreateSerializer, TicketMessageSerializer, MessageAttachmentSerializer

class IsTicketOwnerOrStaff(permissions.BasePermission):
    """
    Allow access if user is ticket creator or staff.
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff or request.user.is_superuser:
            return True
        return obj.creator == request.user


class TicketViewSet(viewsets.ModelViewSet):
    """
    CRUD for tickets.
    - list: users see own tickets; staff see all
    - retrieve: ticket detail plus messages
    - create: create ticket as authenticated user
    - partial_update: staff only (assign, status, priority)
    """
    queryset = Ticket.objects.all().select_related("creator", "assigned_to").prefetch_related("messages", "messages__attachments")
    lookup_field = "reference"  # use reference for nicer URLs
    filterset_fields = ["status", "priority", "creator__username", "assigned_to__username"]
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return TicketCreateSerializer
        return TicketSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return self.queryset
        return self.queryset.filter(creator=user)

    def perform_create(self, serializer):
        # creator is taken from request in serializer.create
        ticket = serializer.save()
        # optionally trigger hooks: notifications, analytics
        # notify_ticket_created(ticket)
        return ticket

    def partial_update(self, request, *args, **kwargs):
        # allow staff to update status / assignment
        instance = self.get_object()
        if not request.user.is_staff and not request.user.is_superuser:
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        return super().partial_update(request, *args, **kwargs)
