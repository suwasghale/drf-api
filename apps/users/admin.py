from django.contrib import admin
from apps.users.models import User, UserActivityLog, PasswordHistory
# Register your models here.
# ✅ Inline: Show password history inside User detail
class PasswordHistoryInline(admin.TabularInline):
    model = PasswordHistory
    extra = 0
    readonly_fields = ("password_hash", "timestamp")
    can_delete = False
    ordering = ("-timestamp",)
    verbose_name_plural = "Password Change History"\

# ✅ Inline: Show latest few user activities inside User detail
class UserActivityLogInline(admin.TabularInline):
    model = UserActivityLog
    extra = 0
    readonly_fields = (
        "action",
        "timestamp",
        "ip_address",
        "user_agent",
        "location",
        "outcome",
    )
    can_delete = False
    ordering = ("-timestamp",)
    show_change_link = False
    verbose_name_plural = "Recent Activity Logs"

    def get_queryset(self, request):
        """Show only last 10 logs for performance."""
        qs = super().get_queryset(request)
        return qs.order_by("-timestamp")[:10]
    
# ✅ Custom User Admin
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "username",
        "email",
        "role",
        "is_active",
        "is_email_verified",
        "is_staff",
        "last_login",
        "date_joined",
    )
    list_filter = ("role", "is_email_verified", "is_staff", "is_superuser", "is_active")
    search_fields = ("username", "email", "display_name")
    ordering = ("username",)
    list_per_page = 30

    inlines = [PasswordHistoryInline, UserActivityLogInline]

    readonly_fields = (
        "last_login",
        "date_joined",
        "failed_login_attempts",
        "last_failed_login_attempt",
    )

    fieldsets = (
        ("Login Info", {
            "fields": ("username", "password")
        }),
        ("Personal Info", {
            "fields": ("display_name", "email", "first_name", "last_name")
        }),
        ("Roles & Permissions", {
            "fields": ("role", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")
        }),
        ("Verification & Security", {
            "fields": (
                "is_email_verified",
                "failed_login_attempts",
                "last_failed_login_attempt",
            )
        }),
        ("Timestamps", {
            "fields": ("last_login", "date_joined"),
            "classes": ("collapse",)
        }),
    )


# ✅ User Activity Log (read-only)
@admin.register(UserActivityLog)
class UserActivityLogAdmin(admin.ModelAdmin):
    list_display = ("user", "action", "timestamp", "ip_address", "outcome")
    list_filter = ("outcome", "timestamp", "user__role")
    search_fields = ("user__username", "action", "ip_address", "location")
    ordering = ("-timestamp",)
    list_select_related = ("user",)
    readonly_fields = (
        "user",
        "action",
        "timestamp",
        "ip_address",
        "user_agent",
        "location",
        "outcome",
        "extra_data",
    )
    list_per_page = 30
    show_full_result_count = False


admin.site.register(PasswordHistory)
