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

    def get_queryset(self):
        """
        Admins see all shipments.
        Normal users see only their own shipments.
        """
        user = self.request.user
        if user.is_staff:
            return self.queryset
        return self.queryset.filter(user=user)

    def perform_create(self, serializer):
        """
        When creating a shipment, auto-attach user from request.
        Only staff (admins) can create shipments.
        """
        if not self.request.user.is_staff:
            raise PermissionError("Only admin can create shipments.")

        serializer.save(user=self.request.user)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """
        Update shipment details (e.g. courier, status, tracking number).
        Automatically updates cache.
        """
        instance = self.get_object()
        response = super().update(request, *args, **kwargs)
        cache.delete(f"shipment_detail:{instance.id}")
        return response

    def retrieve(self, request, *args, **kwargs):
        """Retrieve with cache for better performance."""
        shipment_id = kwargs.get("id")
        cache_key = f"shipment_detail:{shipment_id}"
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)
        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, 60 * 2)  # 2 min TTL
        return response