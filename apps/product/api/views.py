from rest_framework import viewsets, filters, permissions
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Avg, Count, Prefetch
from apps.product.models import Category, Product, ProductSpecification, Review
from apps.product.api.serializers import (
    CategorySerializer, 
    ProductSpecificationSerializer,
    ProductSerializer,
    ReviewSerializer
)

# category viewset
class CategoryViewSet(viewsets.ModelViewSet):
    """
    Provides CRUD operations for product categories.
    Supports nested category serialization.
    """
    queryset = Category.objects.prefetch_related('children').all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "slug" # Use slug for URL lookups like /categories/laptops/

    def get_queryset(self):
        """Return root categories if no parent specified."""
        return Category.objects.filter(parent__isnull=True).prefetch_related('children')


# 🛍 PRODUCT VIEWSET
class ProductViewSet(viewsets.ModelViewSet):
    """
    Handles CRUD operations for products with filtering, search, and ordering.
    """
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"

    # Filtering & Searching
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = {
        "category__slug": ["exact"],
        "brand": ["exact", "icontains"],
        "is_available": ["exact"],
        "price": ["gte", "lte"],
    }
    search_fields = ["name", "sku", "brand", "description"]
    ordering_fields = ["price", "created_at", "stock"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Optimize queryset for performance."""
        return (
            Product.objects.filter(is_available=True)
            .select_related("category")
            .prefetch_related(
                "specifications",
                Prefetch("reviews", queryset=Review.objects.filter(is_approved=True))
            )
        )

# ⚙️ PRODUCT SPECIFICATION VIEWSET
class ProductSpecificationViewSet(viewsets.ModelViewSet):
    """
    Manages specifications tied to a product.
    Typically admin-only.
    """
    queryset = ProductSpecification.objects.select_related("product").all()
    serializer_class = ProductSpecificationSerializer
    permission_classes = [permissions.IsAdminUser]

# ⭐ REVIEW VIEWSET
class ReviewViewSet(viewsets.ModelViewSet):
    """
    Manages product reviews.
    Authenticated users can create reviews.
    """
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        """Filter reviews by product."""
        product_slug = self.request.query_params.get("product")
        qs = Review.objects.select_related("product", "user").filter(is_approved=True)
        if product_slug:
            qs = qs.filter(product__slug=product_slug)
        return qs

    def perform_create(self, serializer):
        """
        Attach logged-in user automatically.
        Prevent multiple reviews per product per user (handled at DB level).
        """
        serializer.save(user=self.request.user)