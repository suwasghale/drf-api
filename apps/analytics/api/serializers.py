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

    def get_formatted_revenue(self, obj):
        """
        Format total revenue with currency and thousand separator.
        """
        return f"Rs. {obj.total_revenue:,.2f}"

    def get_performance_summary(self, obj):
        """
        Optional computed field for dashboard insights.
        Could include growth % or trend direction.
        """
        previous_report = (
            SalesReport.objects.filter(date__lt=obj.date)
            .order_by("-date")
            .first()
        )

        if not previous_report or previous_report.total_revenue == 0:
            growth_rate = None
        else:
            growth_rate = (
                ((obj.total_revenue - previous_report.total_revenue)
                 / previous_report.total_revenue)
                * 100
            )

        return {
            "growth_rate": round(growth_rate, 2) if growth_rate is not None else None,
            "status": (
                "up" if growth_rate and growth_rate > 0
                else "down" if growth_rate and growth_rate < 0
                else "stable"
            )
        }

