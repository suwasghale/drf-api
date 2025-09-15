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