from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'order', 
        'amount', 
        'gateway', 
        'status', 
        'created_at', 
        'updated_at'
    )
    list_filter = (
        'status', 
        'gateway', 
        'created_at'
    )
    search_fields = (
        'order__id', 
        'gateway_ref'
    )
    readonly_fields = (
        'amount', 
        'gateway', 
        'gateway_ref', 
        'created_at', 
        'updated_at'
    )
    raw_id_fields = ('order',)
    
    # Customizes the form layout for adding/editing payments
    fieldsets = (
        (None, {
            'fields': ('order', 'amount', 'gateway', 'status')
        }),
        ('Transaction Details', {
            'fields': ('gateway_ref', 'created_at', 'updated_at'),
            'classes': ('collapse',)  # Collapses the section by default
        })
    )
