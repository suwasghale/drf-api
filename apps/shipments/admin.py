from django.contrib import admin
from .models import Shipment
# register the Shipment model with custom admin interface
@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'order', 
        'user', 
        'status', 
        'courier',
        'estimated_delivery',
        'created_at'
    )
    list_filter = (
        'status', 
        'courier', 
        'created_at'
    )
    search_fields = (
        'order__id__exact',  # Search shipments by the exact order ID
        'user__username',    # Search shipments by the associated user's username
        'tracking_number',   # Search by tracking number
    )
    readonly_fields = (
        'order', 
        'user', 
        'created_at', 
        'updated_at'
    )
    raw_id_fields = ('order', 'user')

    # Group fields into a collapsible section for better organization
    fieldsets = (
        (None, {
            'fields': (('order', 'user'), 'status', 'estimated_delivery')
        }),
        ('Address Information', {
            'fields': ('address', 'city', 'state', 'postal_code', 'country'),
            'classes': ('collapse',)
        }),
        ('Tracking Information', {
            'fields': ('courier', 'tracking_number'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
