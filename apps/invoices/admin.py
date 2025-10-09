from django.contrib import admin
from django.utils.html import format_html
from apps.invoices.models import Invoice

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("invoice_number", "order", "status", "total_amount", "issued_at", "pdf_link")
    list_filter = ("status", "invoice_type")
    search_fields = ("invoice_number", "order__id", "order__user__username")
    readonly_fields = ("invoice_number", "issued_at", "created_at", "updated_at")

    actions = ["regenerate_pdf", "mark_paid"]
