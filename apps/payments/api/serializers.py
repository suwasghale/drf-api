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
    refunded = serializers.SerializerMethodField()

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
            "refunded",
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
            "user": {
                "id": order.user.id,
                "username": order.user.username
            },
            "status": order.status,
            "total_price": order.total_price,
            "created_at": order.created_at,
        }
    
    def get_remaining_balance(self, obj):
        return obj.order.remaining_balance
    
    def get_is_fully_paid(self, obj):
        return obj.order.is_fully_paid
    
    def get_refunded(self, obj):
        # check if this payment has been refunded
        return obj.status == "refunded"


class PaymentCreateSerializer(serializers.ModelSerializer):
    """
    Create new payments with validations and auto-update order status
    """
    # extra fields depending on gateway
    token = serializers.CharField(required=False)   # for Khalti
    ref_id = serializers.CharField(required=False)  # for Esewa

    class Meta:
        model = Payment
        fields = ["order", "amount", "gateway", "gateway_ref", "token", "ref_id"]

    def validate(self, data):
        gateway = data.get("gateway")

        if gateway == "khalti" and not data.get("token"):
            raise serializers.ValidationError({"token": "Token required for Khalti payment"})

        if gateway == "esewa" and not data.get("ref_id"):
            raise serializers.ValidationError({"ref_id": "Reference ID required for eSewa payment"})

        return data

    def create(self, validated_data):
        payment = Payment.objects.create(**validated_data)

        # COD → mark completed immediately
        if payment.gateway == "cod":
            payment.status = "completed"
            payment.save(update_fields=["status"])

        # ✅ Check if the order is now fully paid
        order = payment.order
        if order.is_fully_paid:
            order.status = "paid"
            order.save(update_fields=["status"])

        return payment

class PaymentUpdateSerializer(serializers.ModelSerializer):
    """
    Used by admin/payment gateway callback to update status
    """
    class Meta:
        model = Payment
        fields = ["status", "gateway_ref"]

    def validate_status(self, value):
        if value not in ["pending", "completed", "failed", "refunded"]:
            raise serializers.ValidationError("Invalid status value.")
        return value

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)

        order = instance.order

        # ✅ If payment is refunded or failed → check balance
        if instance.status in ["refunded", "failed"]:
            if order.total_paid == 0:
                order.status = "pending"  # no valid payment left
            else:
                order.status = "pending"  # partially paid, keep it pending
            order.save(update_fields=["status"])

        # ✅ If payments cover total → mark as paid
        elif order.is_fully_paid:
            order.status = "paid"
            order.save(update_fields=["status"])

        return instance
