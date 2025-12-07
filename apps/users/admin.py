from django.contrib import admin
from apps.users.models import User, UserActivityLog, PasswordHistory
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
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

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        # Superuser: see all
        if request.user.is_superuser:
            return qs

        # Staff: cannot see superadmins
        if request.user.is_staff:
            return qs.exclude(role="SUPERADMIN")

        # Vendors/normal users: can only see themselves
        return qs.filter(id=request.user.id)
    
    def has_change_permission(self, request, obj=None):
        # Normal users or vendors cannot change other accounts
        if not request.user.is_staff and not request.user.is_superuser:
            if obj and obj.id != request.user.id:
                return False

        # Staff cannot change superadmin accounts
        if obj and obj.role == "SUPERADMIN" and not request.user.is_superuser:
            return False

        return super().has_change_permission(request, obj)
    
    def get_readonly_fields(self, request, obj=None):
        # Start with default readonly fields
        ro = list(super().get_readonly_fields(request, obj))

        # Staff cannot modify privilege-related fields
        if not request.user.is_superuser:
            ro += ["role", "is_superuser", "is_staff", "groups", "user_permissions"]

        return tuple(ro)


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

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        # Superadmin sees all logs
        if request.user.is_superuser:
            return qs

        # Staff cannot see logs of superadmins
        if request.user.is_staff:
            return qs.exclude(user__role="SUPERADMIN")

        # Normal users/vendors: see their own logs only
        return qs.filter(user=request.user)


# ✅ Password History (read-only)
@admin.register(PasswordHistory)
class PasswordHistoryAdmin(admin.ModelAdmin):
    list_display = ("user", "timestamp")
    list_filter = ("timestamp",)
    search_fields = ("user__username",)
    ordering = ("-timestamp",)
    readonly_fields = ("user", "password_hash", "timestamp")
    list_select_related = ("user",)
    list_per_page = 30
    show_full_result_count = False
    verbose_name_plural = "Password Change History"
    verbose_name = "Password Change History"