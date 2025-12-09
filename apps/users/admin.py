from django.contrib import admin
from apps.users.models import User, UserActivityLog, PasswordHistory
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from core.admin_logging import log_admin_action


class PasswordHistoryInline(admin.TabularInline):
    model = PasswordHistory
    extra = 0
    readonly_fields = ("password_hash", "timestamp")
    can_delete = False
    ordering = ("-timestamp",)
    verbose_name_plural = "Password Change History"


class UserActivityLogInline(admin.TabularInline):
    model = UserActivityLog
    extra = 0
    readonly_fields = (
        "action_type",
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
        qs = super().get_queryset(request)
        return qs.order_by("-timestamp")[:10]


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
        ("Login Info", {"fields": ("username", "password")}),
        ("Personal Info", {"fields": ("display_name", "email", "first_name", "last_name")}),
        (
            "Roles & Permissions",
            {"fields": ("role", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        (
            "Verification & Security",
            {"fields": ("is_email_verified", "failed_login_attempts", "last_failed_login_attempt")},
        ),
        ("Timestamps", {"fields": ("last_login", "date_joined"), "classes": ("collapse",)}),
    )

    # -----------------------------------------------------------------
    #  Restrict queryset
    # -----------------------------------------------------------------
    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs

        if request.user.is_staff:
            return qs.exclude(role="SUPERADMIN")

        return qs.filter(id=request.user.id)

    # -----------------------------------------------------------------
    #  Permission control: Prevent access to superadmin by staff
    # -----------------------------------------------------------------
    def has_change_permission(self, request, obj=None):
        if obj:
            if obj.role == "SUPERADMIN" and not request.user.is_superuser:
                return False

            if not request.user.is_staff and obj.id != request.user.id:
                return False

        return super().has_change_permission(request, obj)

    # -----------------------------------------------------------------
    #  Restrict sensitive fields for staff
    # -----------------------------------------------------------------
    def get_readonly_fields(self, request, obj=None):
        ro = list(super().get_readonly_fields(request, obj))

        if not request.user.is_superuser:
            ro += ["role", "is_superuser", "is_staff", "groups", "user_permissions"]

        return tuple(ro)

    # -----------------------------------------------------------------
    # Prevent delete (staff & vendors)
    # -----------------------------------------------------------------
    def has_delete_permission(self, request, obj=None):
        if not request.user.is_superuser:
            return False

        return super().has_delete_permission(request, obj)

    # -----------------------------------------------------------------
    # Log admin actions
    # -----------------------------------------------------------------
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        log_admin_action(request, obj, "ADMIN_UPDATE")

    def delete_model(self, request, obj):
        log_admin_action(request, obj, "ADMIN_DELETE")
        super().delete_model(request, obj)

    # -----------------------------------------------------------------
    # Remove bulk delete action
    # -----------------------------------------------------------------
    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions

@admin.register(UserActivityLog)
class UserActivityLogAdmin(admin.ModelAdmin):
    list_display = ("user", "action_type", "timestamp", "ip_address", "outcome")
    list_filter = ("outcome", "timestamp", "user__role")
    search_fields = ("user__username", "action_type", "ip_address", "location")
    ordering = ("-timestamp",)
    readonly_fields = (
        "user",
        "action_type",
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

        if request.user.is_superuser:
            return qs

        if request.user.is_staff:
            return qs.exclude(user__role="SUPERADMIN")

        return qs.filter(user=request.user)

    def has_view_permission(self, request, obj=None):
        if obj:
            if obj.user.role == "SUPERADMIN" and not request.user.is_superuser:
                return False
            if not request.user.is_staff and obj.user != request.user:
                return False
        return super().has_view_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions


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

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs

        if request.user.is_staff:
            return qs.exclude(user__role="SUPERADMIN")

        return qs.filter(user=request.user)

    def has_view_permission(self, request, obj=None):
        if obj:
            if obj.user.role == "SUPERADMIN" and not request.user.is_superuser:
                return False
            if not request.user.is_staff and obj.user != request.user:
                return False
        return super().has_view_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions
