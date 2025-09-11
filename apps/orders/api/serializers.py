from rest_framework import serializers 
from apps.orders.models import Order, OrderItem
from apps.payments.models import Payment


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "product", "product_name", "quantity", "price", "get_total"]
        read_only_fields = ["get_total"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total_paid = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    balance_due = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    is_fully_paid = serializers.BooleanField(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "user",
            "status",
            "total_price",
            "total_paid",
            "balance_due",
            "is_fully_paid",
            "created_at",
            "items",
        ]
        read_only_fields = [
            "user",
            "total_price",
            "total_paid",
            "balance_due",
            "is_fully_paid",
            "created_at",
            "items",
        ]


class PaymentInlineSerializer(serializers.ModelSerializer):
    """Lightweight payment info for order detail"""

    class Meta:
        model = Payment
        fields = ["id", "amount", "gateway", "status", "created_at"]


class OrderDetailSerializer(OrderSerializer):
    """Extends OrderSerializer with related payments"""

    payments = PaymentInlineSerializer(many=True, source="payment", read_only=True)

    class Meta(OrderSerializer.Meta):
        fields = OrderSerializer.Meta.fields + ["payments"]
