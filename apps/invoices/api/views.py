from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from django.shortcuts import get_object_or_404
from django.http import FileResponse, HttpResponse

from apps.invoices.models import Invoice
from apps.invoices.api.serializers import InvoiceSerializer, InvoiceCreateSerializer
from apps.invoices.api.services import create_invoice_for_order

class IsOwnerOrAdmin:
    """Simple class-based permission used inline (or implement as DRF Permission)."""
    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or obj.order.user == request.user
    

class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.select_related("order", "created_by").all()
    serializer_class = InvoiceSerializer

    def get_permissions(self):
        # list only for staff, retrieve for owner or staff
        if self.action == "list":
            return [IsAdminUser()]
        if self.action in ["create_from_order"]:
            return [IsAdminUser()]
        return [IsAuthenticated()]