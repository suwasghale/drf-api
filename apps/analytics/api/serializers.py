from rest_framework import serializers
from apps.analytics.models import SalesReport


class SalesReportSerializer(serializers.ModelSerializer):
    """
    Serializer for monthly/daily sales reports.
    Designed for analytics dashboards and admin panels.
    """

    formatted_date = serializers.SerializerMethodField()
    formatted_revenue = serializers.SerializerMethodField()
    performance_summary = serializers.SerializerMethodField()

    class Meta:
        model = SalesReport
        fields = [
            "id",
            "date",
            "formatted_date",
            "total_orders",
            "total_revenue",
            "formatted_revenue",
            "average_order_value",
            "performance_summary",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]


    # ----------------------------------------------------------------
    # CUSTOM FIELD METHODS
    # ----------------------------------------------------------------

    def get_formatted_date(self, obj):
        """
        Return a human-readable date label (e.g. "October 2025").
        """
        return obj.date.strftime("%B %Y")

