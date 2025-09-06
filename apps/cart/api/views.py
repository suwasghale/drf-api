from rest_framework import viewsets, status 
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.cart.models import Cart
from apps.cart.api.serializers import CartSerializer
from apps.cart.services import get_or_create_cart, add_to_cart, remove_from_cart, clear_cart


class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer 
    permission_classes = [IsAuthenticated]

    """
  
    get_queryset()	
    When: For all ModelViewSet actions that interact with a queryset (e.g., list, retrieve, destroy).	
    What: Returns the base queryset of objects available to the view.	
    Why: To filter the list of carts to only show the currently logged-in user's cart, ensuring data privacy.

    perform_create()
    When: After a POST request has been validated but before the serializer saves the new object.	
    What: Provides a hook to modify the save process.	
    Why: To inject the currently logged-in user into the data being saved, correctly assigning ownership of the new cart.
    """

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)