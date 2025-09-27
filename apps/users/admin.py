from django.contrib import admin
from apps.users.models import User, UserActivityLog, PasswordHistory
# Register your models here.
admin.site.register(User)
admin.site.register(UserActivityLog)
admin.site.register(PasswordHistory)
