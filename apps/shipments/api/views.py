from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.core.cache import cache

from apps.shipments.models import Shipment
from apps.shipments.api.serializers import ShipmentSerializer
from apps.orders.models import Order


class ShipmentViewSet(viewsets.ModelViewSet):
    """
    Manages all shipment-related operations:
      - List / Retrieve for admin or user’s own shipments
      - Create shipment for order (admin only)
      - Update status (admin only)
      - Caching and atomicity for updates
    """
    serializer_class = ShipmentSerializer
    queryset = Shipment.objects.select_related("order", "user").all()
    lookup_field = "id"
    permission_classes = [permissions.IsAuthenticated]