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
    def apply(self, request):
        """
        Apply coupon code against a given order_total (and optionally an order id).
        Response contains calculated discount and final_total.
        To persist usage, call commit_redemption endpoint or let Order creation process call commit_redemption.
        """
        serializer = ApplyDiscountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data["code"].strip()
        order_total = serializer.validated_data["order_total"]
        order_id = serializer.validated_data.get("order_id")

        try:
            discount = DiscountService.get_discount_by_code(code)
            # validate business rules
            DiscountService.validate_for_order(discount, Decimal(order_total), user=request.user)
            # compute values
            discount_amount, final_total = DiscountService.apply_discount_to_order(discount, type("X", (), {"total_price": order_total}))
            return Response({"code": discount.code, "discount_amount": str(discount_amount), "final_total": str(final_total)})
        except DiscountValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], url_path="commit", permission_classes=[IsAuthenticated])
    def commit(self, request, pk=None):
        """
        Commits redemption (record + increment usage). Should be invoked when the order is successful.
        Payload: { "order_id": <id>, "applied_amount": "<decimal>" }
        """
        discount = self.get_object()
        order_id = request.data.get("order_id")
        applied_amount = request.data.get("applied_amount")
        if order_id is None or applied_amount is None:
            return Response({"detail": "order_id and applied_amount required"}, status=status.HTTP_400_BAD_REQUEST)

        # lazy import to avoid circular dependency
        from apps.orders.models import Order
        order = get_object_or_404(Order, pk=order_id)

        try:
            redemption = DiscountService.commit_redemption(discount, request.user, order, applied_amount)
            return Response(DiscountRedemptionSerializer(redemption).data)
        except DiscountValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

