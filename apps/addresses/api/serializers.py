from django.db import transaction
from rest_framework import serializers
from phonenumber_field.serializerfields import PhoneNumberField as SerializerPhoneNumberField

from apps.addresses.models import Country, State, Address
from apps.users.models import User


class CountrySerializer(serializers.ModelSerializer):
    """Read-only / simple create serializer for Country."""
    class Meta:
        model = Country
        fields = ["id", "name", "iso_code", "phone_code"]
        read_only_fields = ["id"]


class StateSerializer(serializers.ModelSerializer):
    """State serializer with nested country summary for convenience."""
    country = CountrySerializer(read_only=True)
    country_id = serializers.PrimaryKeyRelatedField(
        queryset=Country.objects.all(), source='country', write_only=True, required=True
    )

    class Meta:
        model = State
        fields = ["id", "name", "country", "country_id"]
        read_only_fields = ["id", "country"]


class AddressSerializer(serializers.ModelSerializer):
    """
    Full featured Address serializer.
    - Nested country/state for reads; write via country_id/state_id.
    - Staff may pass user_id (maps to 'user' via source) to create for other users.
    - Atomic handling of is_default toggle.
    """
    country = CountrySerializer(read_only=True)
    state = StateSerializer(read_only=True)

    country_id = serializers.PrimaryKeyRelatedField(
        queryset=Country.objects.all(), source="country", write_only=True, required=True
    )
    state_id = serializers.PrimaryKeyRelatedField(
        queryset=State.objects.all(), source="state", write_only=True, allow_null=True, required=False
    )

    phone_number = SerializerPhoneNumberField(allow_null=True, required=False)

    # read-only user summary and writeable user_id for staff (maps to user)
    user = serializers.CharField(source="user.username", read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source="user",
        write_only=True,
        required=False,
        help_text="Staff may set user_id to create address for other users."
    )

    class Meta:
        model = Address
        fields = [
            "id",
            "user",
            "user_id",
            "address_type",
            "recipient_name",
            "phone_number",
            "street_address",
            "city",
            "state",
            "state_id",
            "postal_code",
            "country",
            "country_id",
            "is_default",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "state", "country", "created_at", "updated_at"]

    def validate(self, attrs):
        request = self.context.get("request")
        if request is None:
            raise serializers.ValidationError("Request is required in serializer context.")

        # Determine target user:
        target_user = attrs.get("user") or request.user

        # Required fields check
        required_fields = ["recipient_name", "street_address", "city", "postal_code", "country"]
        missing = []
        for f in required_fields:
            # note: country will be present as model instance due to country_id -> country mapping
            if f == "country":
                if not attrs.get("country") and not getattr(self.instance, "country", None):
                    missing.append(f)
            else:
                if not attrs.get(f) and not getattr(self.instance, f, None):
                    missing.append(f)
        if missing:
            raise serializers.ValidationError({ "detail": f"Missing required fields: {', '.join(missing)}" })

        # Duplicate address prevention
        street = (attrs.get("street_address") or getattr(self.instance, "street_address", "")).strip()
        city = (attrs.get("city") or getattr(self.instance, "city", "")).strip()
        postal = (attrs.get("postal_code") or getattr(self.instance, "postal_code", "")).strip()
        country = attrs.get("country") or getattr(self.instance, "country", None)
        address_type = attrs.get("address_type") or getattr(self.instance, "address_type", None)

        qs = Address.objects.filter(
            user=target_user,
            street_address__iexact=street,
            city__iexact=city,
            postal_code__iexact=postal,
            country=country,
            address_type=address_type
        )
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("An identical address already exists for this user and address type.")

        return attrs

    def create(self, validated_data):
        """
        Create address. validated_data may contain 'user' if staff passed user_id.
        Atomic handling of is_default.
        """
        request = self.context.get("request")
        user = validated_data.pop("user", None) or request.user
        is_default = validated_data.pop("is_default", False)

        with transaction.atomic():
            if is_default:
                Address.objects.filter(user=user, is_default=True).update(is_default=False)
            address = Address.objects.create(user=user, is_default=is_default, **validated_data)
        return address

    def update(self, instance, validated_data):
        """
        Update address atomically; allow staff to change owner via 'user' only.
        """
        request = self.context.get("request")
        new_user = validated_data.pop("user", None)
        is_default = validated_data.pop("is_default", None)

        with transaction.atomic():
            if new_user and request.user.is_staff:
                instance.user = new_user

            if is_default is True:
                # unset other defaults for this user
                Address.objects.filter(user=instance.user, is_default=True).exclude(pk=instance.pk).update(is_default=False)
                instance.is_default = True
            elif is_default is False:
                instance.is_default = False

            for attr, val in validated_data.items():
                setattr(instance, attr, val)
            instance.save()
        return instance
