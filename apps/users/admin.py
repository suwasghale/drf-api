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
    
admin.site.register(User)
admin.site.register(UserActivityLog)
admin.site.register(PasswordHistory)
