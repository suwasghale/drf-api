from django.contrib import admin
from apps.addresses.models import Country, State, Address
# register your models here.

# ✅ Inline model for State (editable inside Country)
class StateInline(admin.TabularInline):
    model = State
    extra = 1  # show 1 empty form by default
    fields = ("name",)
    show_change_link = True
    ordering = ("name",)
@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "iso_code", "phone_code", "created_at", "updated_at")
    search_fields = ("name", "iso_code")
    ordering = ("name",)
    list_per_page = 30
    inlines = [StateInline]  # ✅ add state inline

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

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "recipient_name",
        "street_address",
        "city",
        "state",
        "country",
        "postal_code",
        "address_type",
        "is_default",
        "created_at",
    )
    list_filter = ("country", "state", "address_type", "is_default")
    search_fields = (
        "user__username",
        "recipient_name",
        "street_address",
        "city",
        "postal_code",
    )
    autocomplete_fields = ("user", "country", "state")
    list_select_related = ("user", "country", "state")
    ordering = ("-created_at",)
    list_per_page = 30

    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("User & Recipient Info", {
            "fields": ("user", "recipient_name", "phone_number", "email")
        }),
        ("Address Details", {
            "fields": (
                "street_address",
                "city",
                "state",
                "country",
                "postal_code",
                "address_type",
                "is_default"
            )
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    def get_queryset(self, request):
        """
        Optimize queryset for admin — select related fields to reduce DB hits.
        """
        qs = super().get_queryset(request)
        return qs.select_related("user", "country", "state")