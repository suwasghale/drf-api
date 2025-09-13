from django.contrib import admin
from .models import Order, OrderItem

# Define an inline class for OrderItem
# This allows OrderItems to be displayed and edited on the same page as the parent Order.
class OrderItemInline(admin.TabularInline):
    """
    TabularInline displays the inline items in a tabular format.
    You can also use admin.StackedInline for a different layout.
    """
    model = OrderItem
    raw_id_fields = ('product',)  # Use a raw ID field for the product FK for large product lists
    readonly_fields = ('get_total',) # Show the calculated total but make it read-only
    fields = ('product', 'quantity', 'price', 'get_total')
    extra = 0  # Number of empty forms to display, set to 0 to prevent excessive empty forms


# Register the Order model with a custom ModelAdmin
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_price', 'status', 'created_at', 'balance_due', 'is_fully_paid')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'id')
    readonly_fields = ('total_price', 'created_at', 'total_paid', 'balance_due', 'is_fully_paid')
    inlines = [OrderItemInline]

    # Use a custom queryset to optimize query performance
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('items')

    # Add custom method to list display for total paid
    def total_paid_display(self, obj):
        return obj.total_paid
    total_paid_display.short_description = "Total Paid"

    # Add custom method to list display for balance due
    def balance_due_display(self, obj):
        return obj.balance_due
    balance_due_display.short_description = "Balance Due"
    
    # Add a custom method for is_fully_paid to the list display
    def is_fully_paid_display(self, obj):
        return obj.is_fully_paid
    is_fully_paid_display.short_description = "Fully Paid"
    is_fully_paid_display.boolean = True


# Register the OrderItem model separately for a dedicated view
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price', 'get_total')
    list_filter = ('order__status', 'product')
    search_fields = ('order__id__exact', 'product__name')
    raw_id_fields = ('order', 'product')
    readonly_fields = ('price', 'get_total')
