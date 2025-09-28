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

@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "country", "created_at", "updated_at")
    search_fields = ("name", "country__name")
    list_filter = ("country",)
    ordering = ("country", "name")
    list_select_related = ("country",)
    list_per_page = 30

    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (None, {
            "fields": ("country", "name")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

admin.site.register(Address)