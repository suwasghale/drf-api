from django.contrib import admin
from django.utils.html import format_html
from apps.product.models import Category, Product, ProductSpecification

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

    
admin.site.register(Product)