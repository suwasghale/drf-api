from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from django.shortcuts import get_object_or_404
from django.http import FileResponse, HttpResponse

from apps.invoices.models import Invoice
from apps.invoices.api.serializers import InvoiceSerializer, InvoiceCreateSerializer
from apps.invoices.services.services import create_invoice_for_order

class IsOwnerOrAdmin:
    """Simple class-based permission used inline (or implement as DRF Permission)."""
    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or obj.order.user == request.user
    

class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.select_related("order", "created_by").all()
    serializer_class = InvoiceSerializer

    def get_permissions(self):
        # list only for staff, retrieve for owner or staff
        if self.action == "list":
            return [IsAdminUser()]
        if self.action in ["create_from_order"]:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return self.queryset
        # regular users only see invoices for their orders
        return self.queryset.filter(order__user=user)

    @action(detail=False, methods=["post"], url_path="create-from-order", permission_classes=[IsAdminUser])
    def create_from_order(self, request):
        """
        Admin endpoint to force-create invoice for an order:
        payload: { "order_id": <id> }
        """
        order_id = request.data.get("order_id")
        if not order_id:
            return Response({"detail": "order_id required"}, status=status.HTTP_400_BAD_REQUEST)
        from apps.orders.models import Order
        order = get_object_or_404(Order, pk=order_id)
        inv = create_invoice_for_order(order, created_by=request.user, force=True)
        serializer = InvoiceSerializer(inv, context={"request": request})


    @action(detail=True, methods=["get"], url_path="download")
    def download(self, request, pk=None):
        invoice = self.get_object()
        # permission: owner or staff
        if not (request.user.is_staff or invoice.order.user == request.user):
            raise PermissionDenied("Not allowed")

        if not invoice.pdf:
            # Optionally generate sync if missing (this could be long, but fallback)
            from apps.invoices.pdf import generate_invoice_pdf_bytes
            pdf_bytes = generate_invoice_pdf_bytes(invoice)
            filename = f"{invoice.invoice_number or invoice.pk}.pdf"
            invoice.attach_pdf_bytes(filename, pdf_bytes)

            # Return a FileResponse streaming the file
            return FileResponse(invoice.pdf.open("rb"), as_attachment=True, filename=invoice.pdf.name.split("/")[-1])