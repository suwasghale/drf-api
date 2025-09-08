from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from apps.orders.models import Order
from apps.orders.api.serializers import OrderSerializer
from apps.orders.services import create_order_from_cart



class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user = self.request.user).order_by('-created_at')
    
    def perform_create(self, serializer):
        # normal creation is not allowed, use create_order action
        raise NotImplementedError("Use the '/orders/place_order/' endpoint to create orders.")

    @action(detail = False, methods = ['post'], url_path = 'place_order')
    def place_order(self, request):
        try:
            order = create_order_from_cart(request.user)
            serializer = self.get_serializer(order)
            return Response(serializer.data, status = status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({'detail': str(e)}, status = status.HTTP_400_BAD_REQUEST)