from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from phonenumber_field.serializerfields import PhoneNumberField as SerializerPhoneNumberField
from apps.users.models import User, Country, State, Address, UserActivityLog, PasswordHistory


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'date_joined',
            'first_name', 'last_name', 'display_name',
            'is_active', 'is_email_verified', 'last_login',
            'is_staff', 'is_superuser',
        ]
        read_only_fields = [
            'id', 'date_joined', 'last_login',
            'is_active', 'is_email_verified',
            'is_staff', 'is_superuser',
        ]
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, max_length=255)
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name']
    
    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=50)
    password = serializers.CharField(max_length=255,write_only=True)

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["username"] = user.username
        token["email"] = user.email
        token["is_email_verified"] = user.is_email_verified
        return token

# address related serializers
class CountrySerializer(serializers.ModelSerializer):
    """Read-only / simple create serializer for Country."""
    class Meta:
        model = Country
        fields = ["id", "name", "code"]
        read_only_fields = ["id"]

class StateSerializer(serializers.ModelSerializer):
    """State serializer with nested country summary for convenience."""
    country = CountrySerializer(read_only=True)
    country_id = serializers.PrimaryKeyRelatedField(
        queryset=Country.objects.all(), source='country', write_only=True, required=False
    )
    class Meta:
        model = State
        fields = ["id", "name", "country", "country_id"]
        read_only_fields = ["id", "country"]

class AddressSerializer(serializers.ModelSerializer):
    """
    Full featured Address serializer.
    - Uses PhoneNumber serializer field for robust phone parsing/validation.
    - Returns nested country and state objects for convenience (read-only).
    - Allows staff to create addresses for other users by passing `user_id`, otherwise the request user is used.
    - Handles the "is_default" atomic toggle (when you create/update an address and mark it default, all other
      addresses for that user are unset in one transaction).
    - Protects against creating a duplicate identical address (same user + type + street + city + postal + country).
    """
    # Read-only nested representations:
    country = CountrySerializer(read_only=True)
    state = StateSerializer(read_only=True)

    # Write-only ids for linking on create/update:
    country_id = serializers.PrimaryKeyRelatedField(
        queryset=Country.objects.all(), source="country", write_only=True, required=True
    )
    state_id = serializers.PrimaryKeyRelatedField(
        queryset=State.objects.all(), source="state", write_only=True, allow_null=True, required=False
    )

    phone_number = SerializerPhoneNumberField(allow_null=True, required=False)

    user = serializers.CharField(source="user.username", read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
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
        """
         Extra validation:
        - Ensure `recipient_name`, `street_address`, `city`, `postal_code` exist.
        - Prevent exact duplicate addresses for the same user.
        """
        request = self.context.get("request")
        if request is None:
            raise serializers.ValidationError("Request is required in serializer context.")
        # determine user-target: user_id (staff) or request.user
        user = None 
        if "user" in attrs and attrs["user"]:
            # shouldn't happen because user is read-only; user_id is used for write
            user = attrs["user"]
        
        user_id = self.initial_data.get("user_id")
        if user_id and request.user.is_staff:
            # allowed: staff can pass user_id to create on behalf of other users
            user = attrs.get("user") # handled by `user_id` -> `user`
        
        else:
            user = request.user 
        
        # required fields check - Django model enforces but nicer messages here
        required_fields = ["recipient_name", "street_address", "city", "postal_code", "country"]
        missing_fields = [f for f in required_fields if not attrs.get(f) and not (f == "country" and "country_id" in self.initial_data)]
        if missing_fields:
            raise serializers.ValidationError({ "detail": f"Missing required fields: {', '.join(missing_fields)}"})
        
        # Duplicate exact address prevention (unique-ish)
        # Compose a lookup using incoming values or existing instance values
        street = attrs.get("street_address") or getattr(self.instance, "street_address", "")
        city = attrs.get("city") or getattr(self.instance, "city", "")
        postal = attrs.get("postal_code") or getattr(self.instance, "postal_code", "")
        country = attrs.get("country") or getattr(self.instance, "country", None)
        address_type = attrs.get("address_type") or getattr(self.instance, "address_type", None)
        # If country is a PK relation via write field it will be present in attrs['country'] due to source mapping.

        if country is None:
            # country might be provided via country_id; serializer already maps that into attrs['country'].
            country = None

        # Build queryset and exclude self if updating
        qs = Address.objects.filter(user=user, street_address__iexact=street.strip(), city__iexact=city.strip(),
        postal_code__iexact=postal.strip(), country=country, address_type=address_type)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("An identical address already exists for this user and address type.")

        return attrs
    
    def create(self, validated_data):
        """
        Create address with atomic handling of `is_default`.
        If `user_id` provided and request.user.is_staff, create for that user.
        """
        request = self.context.get("request")
        # Determine user: prefer user_id if staff, otherwise request.user
        if validated_data.pop("user", None):
            # shouldn't normally be present; user_id maps to `user` because of source mapping
            user = validated_data.pop("user")
        elif self.initial_data.get("user_id") and request.user.is_staff:
            user = validated_data.pop("user")
        else:
            user = request.user
        is_default = validated_data.pop("is_default", False)

        # Perform create and default toggle in one transaction
        with transaction.atomic():
            if is_default:
                # unset previous defaults for this user
                Address.objects.filter(user=user, is_default=True).update(is_default=False)

            address = Address.objects.create(user=user, is_default=is_default, **validated_data)
        return address

    def update(self, instance, validated_data):
        """
        Support partial / full updates. Handle toggling `is_default` atomically.
        Staff can change `user` only if provided and staff.
        """
        request = self.context.get("request")
        # If a different user is provided via user_id and caller is staff -> allow changing owner
        if "user" in validated_data:
            if request.user.is_staff:
                instance.user = validated_data.pop("user")
            else:
                # ignore any attempt to change user if not staff
                validated_data.pop("user", None)
        
        is_default = validated_data.pop("is_default", None)
        
        with transaction.atomic():
            # If setting new default, unset others first
            if is_default:
                Address.objects.filter(user=instance.user, is_default=True).exclude(pk=instance.pk).update(is_default=False)
                instance.is_default = True
            elif is_default is False and instance.is_default:
                # If explicitly marking this address non-default, allow it
                instance.is_default = False

            # update other fields
            for attr, val in validated_data.items():
                setattr(instance, attr, val)
            instance.save()

        return instance