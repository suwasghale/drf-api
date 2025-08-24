from rest_framework import serializers 
from .models import User 

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'display_name', 'is_active', 'is_email_verified', 'last_login']
        read_only_fields = ['last_login']
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