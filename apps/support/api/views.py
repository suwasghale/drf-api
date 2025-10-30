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

