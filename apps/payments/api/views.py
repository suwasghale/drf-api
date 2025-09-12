from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.payments.api.serializers import (
    PaymentSerializer,
    PaymentDetailSerializer,
    PaymentCreateSerializer,
    PaymentUpdateSerializer,
)
from apps.payments.models import Payment

class PaymentViewSet(viewsets.ModelViewSet):
    """
    NOTE: Handles all CRUD for Payments
    - list: show all user payments
    - retrieve: show detailed payment info
    - create: initiate a payment
    - update/partial_update: update status (admin/gateway only)    """
    queryset = Payment.objects.all().select_related("order", "order__user")
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return self.queryset  # Admins can see all payments
        return self.queryset.filter(order__user=user)  # Users can see their own payments
    
    def get_serializer_class(self):
        if self.action == "list":
            return PaymentSerializer
        
        elif self.action == "retrieve":
            return PaymentDetailSerializer
        
        elif self.action == "create":
            return PaymentCreateSerializer
        
        elif self.action in ["update", "partial_update"]:
            return PaymentUpdateSerializer
        
        return PaymentSerializer
    
    def perform_create(self, serializer): 
        """ Auto-update order status if fully paid """
        payment = serializer.save()
        # update order status automatically if fully paid
        order = payment.order
        if order.is_fully_paid:
            order.status = "paid"
        else:
            order.status = "pending"
        order.save(update_fields=["status"])

    @action(detail = True, methods=["post"], permission_classes=[IsAuthenticated])
    def refund(self, request, pk=None):
        payment = self.get_object()
        if payment.status != "completed":
            return Response({"detail": "Only completed payments can be refunded."}, status=status.HTTP_400_BAD_REQUEST)
        payment.status = "refunded"
        payment.save(update_fields=["status"])
        
        # Optionally, update order status if needed
        order = payment.order
        if order.is_fully_paid:
            order.status = "paid"
        else:
            order.status = "pending"
        order.save(update_fields= ["status"])
        return Response({"detail": "Payment refunded successfully."}, status=status.HTTP_200_OK)