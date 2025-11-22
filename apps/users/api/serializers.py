# apps/users/api/serializers.py
from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

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

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, max_length=255)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name']

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create_user(**validated_data, password=password)
        # Save initial password history if needed
        from apps.users.utils.password_history import save_password_history
        save_password_history(user, user.password)
        return user

class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField(max_length=150)  # username or email
    password = serializers.CharField(max_length=255, write_only=True)

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        # optional: run Django password validators here
        validate_password(value, user=self.context.get("user"))
        return value

class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'display_name', 'profile_image']
        read_only_fields = ['username']  # optionally prevent username changes
