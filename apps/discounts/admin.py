from django.contrib import admin
from apps.discounts.models import Discount

# Register your models here.

@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ("code", "discount_type", "amount", "is_active", "used_count", "usage_limit", "valid_from", "valid_until")
    search_fields = ("code", "description")
    list_filter = ("discount_type", "is_active")
    readonly_fields = ("used_count", "created_at", "updated_at")

