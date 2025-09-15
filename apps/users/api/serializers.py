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