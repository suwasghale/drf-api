from django.contrib import admin
from django.utils.html import format_html
from apps.product.models import Category, Product, ProductSpecification, Review

# -------------------------------
# Inline for ProductSpecification
# -------------------------------
class ProductSpecificationInline(admin.TabularInline):
    """
    Allows adding/editing Product Specifications directly inside Product admin.
    """
    model = ProductSpecification
    extra = 1
    fields = ("key", "value")
    show_change_link = True
# Register your models here.
# -------------------------------
# Category Admin
# -------------------------------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at", "updated_at")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)


# -------------------------------
# Product Admin
# -------------------------------
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "thumbnail_preview",  # 🖼️ Image preview
        "name",
        "sku",
        "brand",
        "category",
        "price",
        "stock",
        "is_available",
        "created_at",
    )
    list_filter = ("category", "brand", "is_available", "free_shipping")
    search_fields = ("name", "sku", "brand", "category__name")
    ordering = ("-created_at",)
    inlines = [ProductSpecificationInline]

    fieldsets = (
        ("Basic Info", {
            "fields": ("sku", "name", "slug", "brand", "category", "description")
        }),
        ("Pricing & Availability", {
            "fields": ("price", "old_price", "discount_percentage", "stock", "is_available")
        }),
        ("Shipping & Warranty", {
            "fields": ("free_shipping", "expected_delivery", "warranty")
        }),
        ("Media", {
            "fields": ("thumbnail", "images")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    readonly_fields = ("created_at", "updated_at")
    prepopulated_fields = {"slug": ("name",)}
    filter_horizontal = ()
    actions = ["mark_as_available", "mark_as_unavailable"]

    # 🖼️ Custom method for thumbnail preview
    def thumbnail_preview(self, obj):
        """
        Displays a small thumbnail preview in the admin list.
        """
        if obj.thumbnail:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 5px;" />', obj.thumbnail.url)
        return "No Image"
    thumbnail_preview.short_description = "Preview"


# -------------------------------
# Review Admin
# -------------------------------
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "rating", "is_verified_purchase", "is_approved", "created_at")
    list_filter = ("rating", "is_verified_purchase", "is_approved", "created_at")
    search_fields = ("product__name", "user__username", "comment")
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("product", "user")