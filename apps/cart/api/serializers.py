from rest_framework import serializers
from apps.cart.models import Cart, CartItem 

class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name', read_only = True)
    subtotal = serializers.ReadOnlyField(read_only = True)

    class Meta:
        model = CartItem 
        fields = ['id', 'product', 'product_name', 'quantity', 'subtotal']

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.ReadOnlyField()

    class Meta:
        model = Cart
        fields = ["id", "user", "items", "total_price"]
        read_only_fields = ["user"]