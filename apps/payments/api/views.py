from rest_framework import viewsets
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