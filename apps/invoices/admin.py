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

    def pdf_link(self, obj):
        if obj.pdf:
            return format_html('<a href="{}" target="_blank">PDF</a>', obj.pdf.url)
        return "-"

    def regenerate_pdf(self, request, queryset):
        from apps.invoices.pdf import generate_invoice_pdf_bytes
        for inv in queryset:
            pdf_bytes = generate_invoice_pdf_bytes(inv)
            inv.attach_pdf_bytes(f"{inv.invoice_number}.pdf", pdf_bytes)
        self.message_user(request, "Selected invoices regenerated.")
    regenerate_pdf.short_description = "Regenerate PDF for selected invoices"

    def mark_paid(self, request, queryset):
        updated = queryset.update(status=Invoice.Statuses.PAID)
        self.message_user(request, f"Marked {updated} invoices as paid.")
    mark_paid.short_description = "Mark selected invoices as paid"
    
