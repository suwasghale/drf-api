from django.contrib import admin
from django.utils.html import format_html
from django.utils.timesince import timesince
from django.utils import timezone
from apps.analytics.models import SalesReport
from apps.analytics.services.reports_service import generate_monthly_sales_report


@admin.register(SalesReport)
class SalesReportAdmin(admin.ModelAdmin):
    """
    Advanced Django admin configuration for SalesReport.
    Optimized for monitoring revenue performance and report auditing.
    """

    # -------------------------------------------------------------------
    # LIST DISPLAY CONFIGURATION
    # -------------------------------------------------------------------
    list_display = (
        "date_display",
        "total_orders",
        "colored_revenue",
        "average_order_value",
        "growth_indicator",
        "last_updated",
    )
    list_display_links = ("date_display",)

    list_filter = (
        ("date", admin.DateFieldListFilter),
    )

    search_fields = ("date",)
    ordering = ("-date",)

    readonly_fields = (
        "date",
        "total_orders",
        "total_revenue",
        "average_order_value",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        ("Report Details", {
            "fields": (
                "date",
                "total_orders",
                "total_revenue",
                "average_order_value",
            )
        }),
        ("Metadata", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )

    date_hierarchy = "date"
