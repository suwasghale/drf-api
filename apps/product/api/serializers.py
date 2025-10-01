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

# ⭐ REVIEW SERIALIZER
class ReviewSerializer(serializers.ModelSerializer):
    """
    Serializes product reviews with username and rating info.
    """
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Review
        fields = [
            "id",
            "username",
            "rating",
            "comment",
            "images",
            "is_verified_purchase",
            "created_at",
        ]
        read_only_fields = ["created_at", "is_verified_purchase"]

# 🛍 PRODUCT SERIALIZER
class ProductSerializer(serializers.ModelSerializer):
    """
    Main product serializer with nested category, specifications, and reviews.
    Adds computed fields like final_price, discount_amount, avg_rating, and review_count.
    """

    category = CategorySerializer(read_only=True)
    specifications = ProductSpecificationSerializer(many=True, read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)

    # Computed fields
    final_price = serializers.SerializerMethodField()
    discount_amount = serializers.SerializerMethodField()
    avg_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "sku",
            "name",
            "slug",
            "description",
            "brand",
            "category",
            "price",
            "old_price",
            "discount_percentage",
            "discount_amount",
            "final_price",
            "stock",
            "is_available",
            "warranty",
            "free_shipping",
            "expected_delivery",
            "thumbnail",
            "images",
            "specifications",
            "reviews",
            "avg_rating",
            "review_count",
            "created_at",
        ]