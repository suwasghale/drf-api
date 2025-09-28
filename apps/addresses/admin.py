from django.contrib import admin
from apps.addresses.models import Country, State, Address
# register your models here.
@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "iso_code", "phone_code", "created_at", "updated_at")
    search_fields = ("name", "iso_code")
    ordering = ("name",)
    list_per_page = 30

    # if you have timestamps in the model
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (None, {
            "fields": ("name", "iso_code", "phone_code")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
admin.site.register(State)
admin.site.register(Address)