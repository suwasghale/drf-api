from rest_framework import serializers
from django.db.models import Avg
from apps.products.models import Category, Product, ProductSpecification, Review
from cloudinary.utils import cloudinary_url


# ================================
# CATEGORY SERIALIZER
# ================================
class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "parent", "children"]

    def get_children(self, obj):
        if obj.children.exists():
            return CategorySerializer(obj.children.all(), many=True).data
        return []


# ================================
# PRODUCT SPECIFICATION SERIALIZER
# ================================
class ProductSpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSpecification
        fields = ["key", "value"]


# ================================
# REVIEW SERIALIZER
# ================================
class ReviewSerializer(serializers.ModelSerializer):
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


# ================================
# PRODUCT SERIALIZER (FINAL + CLEAN)
# ================================
class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    specifications = ProductSpecificationSerializer(many=True, read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)

    # Computed fields
    discount_amount = serializers.SerializerMethodField()
    final_price = serializers.SerializerMethodField()
    avg_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()

    # Image URL helpers
    thumbnail_url = serializers.SerializerMethodField()
    gallery_urls = serializers.SerializerMethodField()

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
            "thumbnail_url",
            "gallery",
            "gallery_url",
            "specifications",
            "reviews",
            "avg_rating",
            "review_count",
            "created_at",
        ]

    # ================================
    # COMPUTED FIELDS
    # ================================
    def get_discount_amount(self, obj):
        return obj.discount_amount

    def get_final_price(self, obj):
        return obj.final_price

    def get_avg_rating(self, obj):
        avg = obj.reviews.aggregate(avg=Avg("rating"))["avg"]
        return round(avg, 1) if avg else 0.0

    def get_review_count(self, obj):
        return obj.reviews.filter(is_approved=True).count()

    # ================================
    # IMAGE URL HELPERS
    # ================================
    def get_thumbnail_url(self, obj):
        if obj.thumbnail:
            url, _ = cloudinary_url(obj.thumbnail.name)
            return url
        return None

    def get_images_url(self, obj):
        if not obj.images:
            return []
        urls = []
        for public_id in obj.images:
            url, _ = cloudinary_url(public_id)
            urls.append(url)
        return urls

class ProductReadSerializer(serializers.ModelSerializer):
    thumbnail_url = serializers.SerializerMethodField()
    images_urls = serializers.SerializerMethodField()
    specifications = ProductSpecificationSerializer(many=True, read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id","sku","name","slug","description","brand","category",
            "price","old_price","discount_percentage","discount_amount","final_price",
            "stock","is_available","warranty","free_shipping","expected_delivery",
            "thumbnail_public_id","thumbnail_url","images","images_urls",
            "specifications","reviews","created_at",
        ]

    def get_thumbnail_url(self, obj):
        return obj.thumbnail_url() if obj.thumbnail_public_id else None

    def get_images_urls(self, obj):
        return obj.images_urls() if obj.images else []
