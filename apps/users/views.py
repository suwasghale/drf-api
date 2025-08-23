from django.shortcuts import render
from rest_framework import viewsets, mixins, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import User
from .serializers import UserSerializer, RegisterSerializer, LoginSerializer
from django.contrib.auth import authenticate

# Create your views here.
# List and Detail Read Only
class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

# register endpoint
class RegisterViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

# "Me" endpoint
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

# login endpoint
class LoginViewSet(viewsets.ViewSet):
    """
    POST /api/login/
    Body: { "username": ".....", "password": "....." }
    """
    permission_classes = [AllowAny]

    def create(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        user = authenticate(username=username, password=password)
        if user:
            user_data = UserSerializer(user).data
            # Remove password from response if serializer didn't already
            user_data.pop('password', None)
            return Response(
                {
                    "status": "success",
                    "message": "User logged in successfully",
                    "user": user_data,
                },
                status=status.HTTP_200_OK
            )
        return Response(
            {"status": "error", 
             "message": "Invalid credentials"
             },
            status=status.HTTP_401_UNAUTHORIZED
        )