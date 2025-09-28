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
    
    
admin.site.register(User)
admin.site.register(UserActivityLog)
admin.site.register(PasswordHistory)
