from django.contrib import admin
from .models import User, UserActivityLog, PasswordHistory
# Register your models here.
admin.site.register(User)
admin.site.register(UserActivityLog)
admin.site.register(PasswordHistory)
