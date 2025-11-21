from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from phonenumber_field.serializerfields import PhoneNumberField as SerializerPhoneNumberField
from apps.users.models import User, UserActivityLog, PasswordHistory


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'display_name', 'role', 'is_email_verified',
            'is_active', 'last_login', 'date_joined'
        ]
        read_only_fields = [
            'id', 'is_active', 'is_email_verified',
            'last_login', 'date_joined', 'role',
        ]

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name']

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create_user(**validated_data, password=password)

        # Log password history
        PasswordHistory.objects.create(user=user, password_hash=password)

        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token["username"] = user.username
        token["email"] = user.email
        token["role"] = user.role
        token["is_email_verified"] = user.is_email_verified
        token["is_locked"] = user.is_locked

        return token

