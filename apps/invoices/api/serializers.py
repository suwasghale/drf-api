from rest_framework import serializers
from apps.invoices.models import Invoice

class InvoiceSerializer(serializers.ModelSerializer):
    order_id = serializers.IntegerField(source='order.id', read_only=True)
    pdf_url = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = [
            "id", "invoice_number", "invoice_type", "status", "order_id",
            "subtotal", "tax_amount", "total_amount", "currency",
            "billing_address", "shipping_address", "issued_at", "due_date",
            "pdf_url", "created_at", "updated_at"
        ]
        read_only_fields = fields
# apps/invoices/serializers.py
from rest_framework import serializers
from apps.invoices.models import Invoice

class InvoiceSerializer(serializers.ModelSerializer):
    order_id = serializers.IntegerField(source='order.id', read_only=True)
    pdf_url = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = [
            "id", "invoice_number", "invoice_type", "status", "order_id",
            "subtotal", "tax_amount", "total_amount", "currency",
            "billing_address", "shipping_address", "issued_at", "due_date",
            "pdf_url", "created_at", "updated_at"
        ]
        read_only_fields = fields

    def get_pdf_url(self, obj):
        request = self.context.get("request")
        if obj.pdf:
            return request.build_absolute_uri(obj.pdf.url) if request else obj.pdf.url
        return None

class InvoiceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = ["order", "invoice_type", "due_date"]
        # Creation will be routed to service; keep minimal