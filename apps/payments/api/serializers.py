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
    """
    This defines a field named order, but its value is not directly taken from a model field.
    SerializerMethodField indicates that the field's value will be populated by calling a method on the serializer itself.
    """
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
    """
    The given is the method for the order = serializers.SerializerMethodField() field. DRF automatically looks for a method named get_<field_name>.
    It takes self and the object being serialized (obj, which is a Payment instance).
    It returns a dictionary containing specific details from the related order object, creating a nested representation of the order information.
    """
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


class PaymentCreateSerializer(serializers.ModelSerializer):
    """
     Create new payments with validations
    """
    class Meta:
        model = Payment
        fields = ["order", "amount", "gateway", "gateway_ref"]

    def validate(self, attrs):
        order = attrs["order"]
        amount = attrs["amount"]

        if amount <= 0:
            raise serializers.ValidationError("Amount must be greater than 0.")

        if amount > order.remaining_balance:
            raise serializers.ValidationError(
                f"Amount {amount} exceeds remaining balance {order.remaining_balance}."
            )

        return attrs

    def create(self, validated_data):
        payment = Payment.objects.create(**validated_data)

        # Business rule: COD → mark completed immediately
        if payment.gateway == "cod":
            payment.status = "completed"
            payment.save(update_fields=["status"])

        return payment