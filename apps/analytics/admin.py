from django.contrib import admin
from django.utils.html import format_html
from django.utils.timesince import timesince
from django.utils import timezone
from apps.analytics.models import SalesReport
from apps.analytics.services.report_service import generate_monthly_sales_report

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


    # -------------------------------------------------------------------
    # CUSTOM DISPLAY METHODS
    # -------------------------------------------------------------------

    def date_display(self, obj):
        """Readable month name (e.g. October 2025)."""
        return obj.date.strftime("%B %Y")
    date_display.short_description = "Report Month"

    def colored_revenue(self, obj):
        """Show revenue with color intensity based on value."""
        color = "#2ecc71" if obj.total_revenue > 0 else "#e74c3c"
        return format_html(
            f"<b style='color:{color};'>Rs. {obj.total_revenue:,.2f}</b>"
        )
    colored_revenue.short_description = "Total Revenue"

    def growth_indicator(self, obj):
        """
        Compare this month with previous month.
        Uses simple growth rate logic (can expand via analytics service).
        """
        prev = (
            SalesReport.objects.filter(date__lt=obj.date)
            .order_by("-date")
            .first()
        )
        if not prev or prev.total_revenue == 0:
            return format_html("<span style='color:gray;'>–</span>")

        growth = ((obj.total_revenue - prev.total_revenue) / prev.total_revenue) * 100
        color = "#2ecc71" if growth > 0 else "#e74c3c" if growth < 0 else "#7f8c8d"
        icon = "▲" if growth > 0 else "▼" if growth < 0 else "■"
        return format_html(
            f"<span style='color:{color}; font-weight:bold;'>{icon} {growth:.2f}%</span>"
        )
    growth_indicator.short_description = "Growth vs Previous"

    def last_updated(self, obj):
        """Show how long ago this report was updated."""
        return f"{timesince(obj.updated_at)} ago"
    last_updated.short_description = "Last Updated"


    # -------------------------------------------------------------------
    # ADMIN ACTIONS
    # -------------------------------------------------------------------

    actions = ["regenerate_latest_report", "export_to_csv"]

    def regenerate_latest_report(self, request, queryset):
        """
        Regenerate current month’s sales report (manual trigger).
        """
        generate_monthly_sales_report()
        self.message_user(request, "✅ Monthly sales report regenerated successfully.")
    regenerate_latest_report.short_description = "🔁 Recalculate Current Month Report"

    def export_to_csv(self, request, queryset):
        """
        Export selected reports as CSV (for finance team).
        """
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="sales_reports.csv"'

        writer = csv.writer(response)
        writer.writerow(["Date", "Total Orders", "Total Revenue", "Average Order Value"])

        for report in queryset:
            writer.writerow([
                report.date.strftime("%Y-%m-%d"),
                report.total_orders,
                f"{report.total_revenue:.2f}",
                f"{report.average_order_value:.2f}",
            ])

        return response
    export_to_csv.short_description = "⬇️ Export Selected Reports to CSV"

    # -------------------------------------------------------------------
    # PERFORMANCE OPTIMIZATION
    # -------------------------------------------------------------------

    def get_queryset(self, request):
        """
        Optimize admin queryset.
        Prefetch and order by date for fast rendering.
        """
        qs = super().get_queryset(request)
        return qs.defer("created_at").order_by("-date")

    # -------------------------------------------------------------------
    # PERMISSIONS CONTROL
    # -------------------------------------------------------------------

    def has_add_permission(self, request):
        """
        Reports are auto-generated by services (not manually created).
        """
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        """
        Prevent accidental data loss — allow only superusers to delete.
        """
        return request.user.is_superuser