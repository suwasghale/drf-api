from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone

from apps.notifications.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Custom Django admin for managing notifications.
    Optimized for large data (indexed, search, filters, actions).
    """

    # ------------------- BASIC CONFIG -------------------
    list_display = (
        "id",
        "user_display",
        "title",
        "notification_type",
        "level_colored",
        "is_read",
        "created_at",
        "read_at",
    )
    list_display_links = ("id", "title")

    list_filter = (
        "notification_type",
        "level",
        "is_read",
        ("created_at", admin.DateFieldListFilter),
    )

    search_fields = (
        "title",
        "message",
        "user__username",
        "user__email",
        "notification_type",
    )

    ordering = ("-created_at",)
    date_hierarchy = "created_at"

    readonly_fields = (
        "created_at",
        "updated_at",
        "read_at",
    )

    autocomplete_fields = ["user"]

    fieldsets = (
        ("Notification Info", {
            "fields": (
                "user",
                "title",
                "message",
                "notification_type",
                "level",
            )
        }),
        ("Status & Timestamps", {
            "fields": (
                "is_read",
                "read_at",
                "created_at",
                "updated_at",
            )
        }),
    )

    # ------------------- DISPLAY HELPERS -------------------

    def user_display(self, obj):
        """Return username + email with link."""
        return format_html(
            f'<b>{obj.user.username}</b><br><small>{obj.user.email}</small>'
        )
    user_display.short_description = "User"

    def level_colored(self, obj):
        """Color-coded severity badge."""
        color_map = {
            "info": "#3498db",
            "success": "#2ecc71",
            "warning": "#f1c40f",
            "error": "#e74c3c",
        }
        color = color_map.get(obj.level, "#7f8c8d")
        return format_html(
            f'<span style="background-color:{color}; color:white; padding:2px 8px; border-radius:4px; font-size:12px;">{obj.level.title()}</span>'
        )
    level_colored.short_description = "Level"

    # ------------------- CUSTOM ACTIONS -------------------

    actions = ["mark_as_read", "mark_as_unread"]

    def mark_as_read(self, request, queryset):
        """Admin bulk action to mark notifications as read."""
        count = queryset.update(is_read=True, read_at=timezone.now())
        self.message_user(request, f"{count} notifications marked as read.")
    mark_as_read.short_description = "✅ Mark selected as Read"

    def mark_as_unread(self, request, queryset):
        """Admin bulk action to mark notifications as unread."""
        count = queryset.update(is_read=False, read_at=None)
        self.message_user(request, f"{count} notifications marked as unread.")
    mark_as_unread.short_description = "🔄 Mark selected as Unread"
