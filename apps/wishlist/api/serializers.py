from rest_framework import serializers
from apps.wishlist.models import Wishlist, WishlistItem
from apps.product.serializers import ProductSerializer

class WishlistItemSerializers(serializers.ModelSerializer):
    product = ProductSerializer(read_only = True)

    class Meta:
        model = WishlistItem
        fields = ['id', 'product', 'added_at']

class WishlistSerializer(serializers.ModelSerializer):
    items = WishlistItemSerializers(many = True, read_only = True)

    class Meta:
        model = Wishlist
        fields = ['id', 'user', 'items', 'created_at']
        read_only_fields = ['user']