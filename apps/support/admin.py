# apps/support/admin.py
from django.contrib import admin
from django.utils.html import format_html
from apps.support.models import Ticket, TicketMessage, MessageAttachment

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("reference", "title", "creator", "assigned_to", "status", "priority", "created_at", "last_activity_at")
    list_filter = ("status", "priority", "is_public")
    search_fields = ("reference", "title", "creator__username", "assigned_to__username")
    readonly_fields = ("reference", "created_at", "updated_at", "last_activity_at")
    ordering = ("-created_at",)
    raw_id_fields = ("creator", "assigned_to", "order")
    fieldsets = (
        ("Basic", {"fields": ("reference", "title", "description", "tags")}),
        ("Relations", {"fields": ("creator", "assigned_to", "order")}),
        ("Status & Priority", {"fields": ("status", "priority", "is_public", "sla_due_at")}),
        ("Timestamps", {"fields": ("created_at", "updated_at", "last_activity_at")}),
    )

