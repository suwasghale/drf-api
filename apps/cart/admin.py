from django.contrib import admin
from apps.cart.models import Cart, CartItem

# Create an Inline class for CartItem.
# This class defines how CartItems will be displayed within the CartAdmin.
class CartItemInline(admin.TabularInline):
    # Link the inline to the CartItem model.
    model = CartItem
    # Define the fields to display for each CartItem in the inline table.
    fields = ('product', 'quantity')
    # Use 'raw_id_fields' for the product to replace the dropdown with a search widget.
    # This is much more efficient for a large number of products.
    raw_id_fields = ('product',)
    # Display one extra empty form for adding a new CartItem.
    extra = 1

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    # Display these fields in the list view of all carts.
    list_display = ('user', 'created_at', 'updated_at', 'get_total_price')
    # Add a filter sidebar for the 'user' field.
    list_filter = ('user',)
    # Make the list searchable by the username.
    search_fields = ('user__username',)
    # Include the CartItemInline on the Cart's detail page.
    inlines = [CartItemInline]

    # Add the 'total_price' property as a displayable field.
    # The 'short_description' provides a user-friendly column header.
    def get_total_price(self, obj):
        return obj.total_price
    get_total_price.short_description = "Total Price"

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    # Since we are managing CartItems through the Cart inline,
    # the standalone CartItemAdmin is less critical, but still useful for bulk actions.
    list_display = ('cart', 'product', 'quantity')
    list_filter = ('cart', 'product')
    search_fields = ('product__name', 'cart__user__username')