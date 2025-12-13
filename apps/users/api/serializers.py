# apps/users/api/serializers.py

from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from apps.users.utils.password_history import save_password_history

User = get_user_model()


# -----------------------------------------------------------
# 1. Base Safe User Serializer (returned to frontend)
# -----------------------------------------------------------
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'date_joined',
            'first_name', 'last_name', 'display_name', 'profile_image',
            'is_active', 'is_email_verified', 'last_login',
            'is_staff', 'is_superuser', 'role',
        ]
        read_only_fields = [
            'id', 'date_joined', 'last_login',
            'is_active', 'is_email_verified',
            'is_staff', 'is_superuser', 'role',
        ]


# -----------------------------------------------------------
# 2. Registration Serializer
# -----------------------------------------------------------
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        max_length=255,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name']

    def validate_email(self, value):
        value = value.lower().strip()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value

    def validate_password(self, value):
        validate_password(value)  # Django built-in validators
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        validated_data["email"] = validated_data["email"].lower()

        user = User.objects.create_user(**validated_data, password=password)

        # Save password in history
        save_password_history(user, user.password)

        return user


# -----------------------------------------------------------
# 3. Login Serializer (username or email)
# -----------------------------------------------------------
class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField(max_length=150)  # username or email
    password = serializers.CharField(max_length=255, write_only=True)
    user = None

    def validate(self, attrs):
        identifier = attrs.get("identifier")
        password = attrs.get("password")

        # Try email first (case-insensitive)
        try:
            user_obj = User.objects.get(email__iexact=identifier)
            username = user_obj.username
        except User.DoesNotExist:
            username = identifier  # fallback to username login

        user = authenticate(username=username, password=password)

        if not user:
            raise serializers.ValidationError(_("Invalid credentials."))

        if not user.is_active:
            raise serializers.ValidationError(_("This account is inactive."))

        self.user = user
        return attrs


# -----------------------------------------------------------
# 4. Password Reset Request
# -----------------------------------------------------------
class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        value = value.lower()
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user found with this email.")
        return value


# -----------------------------------------------------------
# 5. Password Reset Confirmation
# -----------------------------------------------------------
class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value


# -----------------------------------------------------------
# 6. Change Password
# -----------------------------------------------------------
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = self.context.get("user")

        if not user.check_password(attrs["old_password"]):
            raise serializers.ValidationError("Old password is incorrect.")

        validate_password(attrs["new_password"], user)

        return attrs

    def save(self):
        user = self.context.get("user")
        user.set_password(self.validated_data["new_password"])
        user.save()

        save_password_history(user, user.password)

        return user


# -----------------------------------------------------------
# 7. Profile Update
# -----------------------------------------------------------
class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name',
            'display_name', 'profile_image',
        ]
        read_only_fields = ['username']  # optional
