from rest_framework import serializers
from apps.shipments.models import Shipment


class ShipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shipment
        fields = [
            "id", "order", "user", "address", "city", "state", "postal_code", "country",
            "courier", "tracking_number", "status", "estimated_delivery",
            "created_at", "updated_at"
        ]
        read_only_fields = ["user", "created_at", "updated_at"]
