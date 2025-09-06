from rest_framework import serializers
from apps.cart.models import Cart, CartItem 

class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name', read_only = True)
    subtotal = serializers.ReadOnlyField(read_only = True)

    class Meta:
        model = CartItem 
        fields = ['id', 'product', 'product_name', 'quantity', 'subtotal']

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True) # creates a nested serializer, where the items field in the Cart response will be a list of serialized CartItem objects, each formatted by the CartItemSerializer.
    total_price = serializers.ReadOnlyField()

    class Meta: # A special class used to provide metadata about the serializer's configuration.
        model = Cart
        fields = ["id", "user", "items", "total_price"]
        read_only_fields = ["user"]