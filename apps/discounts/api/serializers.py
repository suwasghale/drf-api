from rest_framework import serializers
from apps.discounts.models import Discount
from apps.discounts.models_user_usage import DiscountRedemption
from django.utils import timezone
from decimal import Decimal

class DiscountSerializer(serializers.ModelSerializer):
    remaining_uses = serializers.SerializerMethodField()

    class Meta:
        model = Discount
        fields = [
            "id", "code", "description", "discount_type", "amount",
            "min_order_value", "usage_limit", "used_count", "per_user_limit",
            "is_active", "valid_from", "valid_until",
            "remaining_uses", "created_at", "updated_at"
        ]
        read_only_fields = ["used_count", "created_at", "updated_at"]

    def get_remaining_uses(self, obj):
        return obj.remaining_global_uses()

class ApplyDiscountSerializer(serializers.Serializer):
    """
    Input serializer for applying coupon to an order/cart.
    """
    code = serializers.CharField(max_length=50)
    order_id = serializers.IntegerField(required=False)  # optional; service may accept a cart object instead
    # Provide the pre-discount amount as a double-check (server will recalc)
    order_total = serializers.DecimalField(max_digits=12, decimal_places=2)



class DiscountRedemptionSerializer(serializers.ModelSerializer):
    discount = DiscountSerializer(read_only=True)
    class Meta:
        model = DiscountRedemption
        fields = ["id", "discount", "user", "order", "amount", "created_at"]
        read_only_fields = fields