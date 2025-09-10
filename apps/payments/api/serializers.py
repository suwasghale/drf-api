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