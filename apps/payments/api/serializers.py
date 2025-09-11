from rest_framework import serializers
from apps.payments.models import Payment 
from apps.orders.models import Order


class PaymentSerializer(serializers.ModelSerializer):
    """
    Base serializer: used for listing all payments
    """
    order_id = serializers.IntegerField(source="order.id", read_only=True)
    user = serializers.CharField(source="order.user.username", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "order_id",
            "user",
            "amount",
            "gateway",
            "gateway_ref",
            "status",
            "created_at",
            "updated_at",
        ]

class PaymentDetailSerializer(serializers.ModelSerializer):
    """
    Detail serializer with nested order information
    """
    order = serializers.SerializerMethodField()
    remaining_balance = serializers.SerializerMethodField()
    is_fully_paid = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            "id",
            "order",
            "amount",
            "gateway",
            "gateway_ref",
            "status",
            "created_at",
            "updated_at",
            "remaining_balance",
            "is_fully_paid",
        ]

    def get_order(self, obj):
        order = obj.order 
        return {
            "id": order.id,
            "user": order.user.username,
            "status": order.status,
            "total_price": order.total_price,
            "created_at": order.created_at,
        }
    
    def get_remaining_balance(self, obj):
        return obj.order.remaining_balance
    
    def get_is_fully_paid(self, obj):
        return obj.order.is_fully_paid

