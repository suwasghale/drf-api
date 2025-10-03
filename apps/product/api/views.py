from rest_framework import viewsets, filters, permissions
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Avg, Count, Prefetch, Q
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django.conf import settings
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.throttling import ScopedRateThrottle
from apps.product.models import Category, Product, ProductSpecification, Review
from apps.product.api.serializers import (
    CategorySerializer, 
    ProductSpecificationSerializer,
    ProductSerializer,
    ReviewSerializer
)
from apps.product.api.pagination import StandardResultsSetPagination

# TTL for anonymous caching (seconds). Use a short TTL so updates propagate quickly.
CACHE_TTL = 60 * 2  # 2 minutes

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

 # -------- dynamic queryset --------
   def get_queryset(self):
        """
        Return optimized queryset with dynamic filters applied from query params.
        Use annotated aggregate fields for avg_rating & review_count.
        """
        qs = self.base_queryset
        request = getattr(self, "request", None)

        # Public users should see only available products
        if not request or not (request.user and request.user.is_staff):
            qs = qs.filter(is_available=True)

        # apply common query parameters
        q = request.query_params.get("q") if request else None
        if q:
            # simple DB search; for heavy use switch to full-text or external search engine
            qs = qs.filter(
                Q(name__icontains=q) | Q(description__icontains=q) | Q(sku__icontains=q) | Q(brand__icontains=q)
            )

        min_price = request.query_params.get("min_price")
        max_price = request.query_params.get("max_price")
        min_rating = request.query_params.get("min_rating")
        brand = request.query_params.get("brand")
        in_stock = request.query_params.get("in_stock")

        if brand:
            qs = qs.filter(brand__iexact=brand)
        if min_price:
            try:
                qs = qs.filter(price__gte=float(min_price))
            except (ValueError, TypeError):
                pass
        if max_price:
            try:
                qs = qs.filter(price__lte=float(max_price))
            except (ValueError, TypeError):
                pass
        if min_rating:
            try:
                qs = qs.filter(avg_rating__gte=float(min_rating))
            except (ValueError, TypeError):
                pass
        if in_stock is not None:
            if in_stock.lower() in ("1", "true", "yes"):
                qs = qs.filter(stock__gt=0)
            elif in_stock.lower() in ("0", "false", "no"):
                qs = qs.filter(stock__lte=0)

        return qs.order_by(*self.ordering)

    # ---------- caching for anonymous users ----------
   def list(self, request, *args, **kwargs):
        """
        Cached for anonymous users. Cache key includes full path (querystring).
        Admins & authenticated users get uncached, always fresh data.
        """
        if not request.user.is_authenticated:
            cache_key = f"product_list:{request.get_full_path()}"
            cached = cache.get(cache_key)
            if cached is not None:
                return Response(cached)

            resp = super().list(request, *args, **kwargs)
            # store only serialized data (not the response object)
            cache.set(cache_key, resp.data, CACHE_TTL)
            return resp

        return super().list(request, *args, **kwargs)
   
   def retrieve(self, request, *args, **kwargs):
        # detail caching for anonymous users
        slug = kwargs.get("slug") or kwargs.get("pk")
        if not request.user.is_authenticated:
            cache_key = f"product_detail:{slug}"
            cached = cache.get(cache_key)
            if cached is not None:
                return Response(cached)

            resp = super().retrieve(request, *args, **kwargs)
            cache.set(cache_key, resp.data, CACHE_TTL)
            return resp

        return super().retrieve(request, *args, **kwargs)

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