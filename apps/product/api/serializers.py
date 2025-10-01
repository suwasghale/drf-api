from rest_framework import serializers
from django.db.models import Avg, Count
from apps.product.models import Category, Product, ProductSpecification, Review


# 🏷 CATEGORY SERIALIZER
class CategorySerializer(serializers.ModelSerializer):
    """
    Serializes category with support for nested children.
    Example:
    {
        "name": "Laptops",
        "slug": "laptops",
        "children": [
            { "name": "Gaming Laptops", ... }
        ]
    }
    """
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "parent", "children"]

    def get_children(self, obj):
        """Recursively serialize subcategories."""
        if obj.children.exists():
            return CategorySerializer(obj.children.all(), many=True).data
        return []


# ⚙️ PRODUCT SPECIFICATION SERIALIZER
class ProductSpecificationSerializer(serializers.ModelSerializer):
    """
    Serializes product technical details.
    Example:
    { "key": "RAM", "value": "16GB DDR5" }
    """

    class Meta:
        model = ProductSpecification
        fields = ["key", "value"]

