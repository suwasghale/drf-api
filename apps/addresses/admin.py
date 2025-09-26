from django.contrib import admin
from apps.addresses.models import Country, State, Address
# Register your models here.
admin.site.register(Country)
admin.site.register(State)
admin.site.register(Address)