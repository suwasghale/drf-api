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
admin.site.register(Category)
admin.site.register(Product)