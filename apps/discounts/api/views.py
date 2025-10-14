from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from apps.discounts.models import Discount, DiscountRedemption
from apps.discounts.api.serializers import (
    DiscountSerializer,
    ApplyDiscountSerializer,
    DiscountRedemptionSerializer,
)
from apps.discounts.services.discount_service import DiscountService, DiscountValidationError

class DiscountViewSet(viewsets.ModelViewSet):
    """
    Admin CRUD for discounts. Public read allowed for active coupons listing.
    """
    queryset = Discount.objects.all().order_by("-created_at")
    serializer_class = DiscountSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]  # public can list and get metadata (you may restrict to staff if desired)
        return [IsAdminUser()]

    @action(detail=False, methods=["post"], url_path="apply", permission_classes=[IsAuthenticated])

