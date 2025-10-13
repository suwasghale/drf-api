from django.contrib import admin
from apps.discounts.models import Discount
from apps.discounts.models_user_usage import DiscountRedemption

# Register your models here.

@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ("code", "discount_type", "amount", "is_active", "used_count", "usage_limit", "valid_from", "valid_until")
    search_fields = ("code", "description")
    list_filter = ("discount_type", "is_active")
    readonly_fields = ("used_count", "created_at", "updated_at")

@admin.register(DiscountRedemption)
class DiscountRedemptionAdmin(admin.ModelAdmin):
    list_display = ("discount", "user", "order", "amount", "created_at")
    search_fields = ("discount__code", "user__username", "order__id")
    list_filter = ("discount",)
