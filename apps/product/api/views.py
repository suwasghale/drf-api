from rest_framework import viewsets, filters, permissions
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Avg, Count, Prefetch, Q
from rest_framework.throttling import ScopedRateThrottle
from apps.product.models import Category, Product, ProductSpecification, Review
from apps.product.api.serializers import (
    CategorySerializer, 
    ProductSpecificationSerializer,
    ProductSerializer,
    ReviewSerializer
)
from apps.product.api.pagination import StandardResultsSetPagination

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
    Production-grade product API:
      - optimized queryset with select_related / prefetch_related
      - annotated avg_rating & review_count (only approved reviews)
      - public read endpoints are cached for anonymous users
      - admin-only write operations
      - search, filters, ordering, pagination
      - admin-only bulk stock updates (atomic + bulk_update)
    """
   serializer_class = ProductSerializer
   lookup_field = "slug"
   pagination_class = StandardResultsSetPagination
   throttle_scope = "product_browse"
   throttle_classes = [ScopedRateThrottle]

    # static base queryset: annotate aggregated fields to avoid per-instance DB hits
   base_queryset = (
        Product.objects.select_related("category")
        .prefetch_related(
            "specifications",
            Prefetch("reviews", queryset=Review.objects.filter(is_approved=True))
        )
        .annotate(
            avg_rating=Avg("reviews__rating", filter=Q(reviews__is_approved=True)),
            review_count=Count("reviews", filter=Q(reviews__is_approved=True)),
        )
    )

    # Filter / Search / Ordering config
   filter_backends = [filters.SearchFilter, filters.OrderingFilter, filters.DjangoFilterBackend]
   search_fields = ["name", "sku", "brand", "description"]
   ordering_fields = ["price", "created_at", "stock", "review_count"]
   ordering = ["-created_at"]

   filterset_fields = {
        "category__slug": ["exact"],
        "brand": ["exact", "icontains"],
        "is_available": ["exact"],
        "price": ["gte", "lte"],
        "discount_percentage": ["gte"],
    }

 # -------- permissions --------
   def get_permissions(self):
        # read (list/retrieve/search) public
        if self.action in ["list", "retrieve", "search", "discounted", "featured", "by_category"]:
            return [permissions.AllowAny()]
        # admin-only for create/update/delete/bulk operations
        if self.action in ["create", "update", "partial_update", "destroy", "bulk_update_stock", "set_availability"]:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

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