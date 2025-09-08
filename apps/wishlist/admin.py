from django.contrib import admin
from apps.wishlist.models import Wishlist, WishlistItem

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    # Display these fields in the list view
    list_display = ('user', 'created_at')
    # Add a filter sidebar for the 'user' field
    list_filter = ('user',)
    # Make the list searchable by the 'user' field
    search_fields = ('user__username',)

@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    # Display these fields in the list view
    list_display = ('wishlist', 'product', 'added_at')
    # Add a filter sidebar for the 'wishlist' and 'product' fields
    list_filter = ('wishlist', 'product')
    # Make the list searchable by the 'product' name
    search_fields = ('product__name',)