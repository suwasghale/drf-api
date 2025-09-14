from django.contrib import admin
from .models import User, UserActivityLog, PasswordHistory, Country, State, Address
# Register your models here.
admin.site.register(User)
admin.site.register(UserActivityLog)
admin.site.register(PasswordHistory)
admin.site.register(Country)
admin.site.register(State)
admin.site.register(Address)