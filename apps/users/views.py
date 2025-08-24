from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings

from rest_framework_simplejwt.tokens import RefreshToken, UntypedToken
from rest_framework_simplejwt.backends import TokenBackend
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

from .serializers import RegisterSerializer
from .utils.email import send_verification_email

User = get_user_model()


class UserViewSet(viewsets.ViewSet):
    """
    Handles registration, email verification, and user profile.
    """

    permission_classes = [AllowAny]

    # ------------------------
    # Register user
    # ------------------------
    @action(detail=False, methods=['post'], url_path='register')
    def register(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        user.is_active = True  # optional: allow login before verification
        user.save(update_fields=['is_active'])

        # Generate JWT access token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        # Build verification URL
        verification_url = request.build_absolute_uri(
            reverse('users-verify-email') + f"?token={access_token}"
        )

        # Send verification email
        send_verification_email(user.email, user.username, verification_url)

        return Response(
            {"status": "success", "message": "User registered. Check your email to verify."},
            status=status.HTTP_201_CREATED
        )

    # ------------------------
    # Email verification
    # ------------------------
    @action(detail=False, methods=['get'], url_path='verify-email', permission_classes=[AllowAny])
    def verify_email(self, request):
        token = request.query_params.get('token')
        if not token:
            return Response({"status": "error", "message": "Token missing"}, status=status.HTTP_400_BAD_REQUEST)

        token = str(token).strip()

        try:
            # Validate token signature & expiration
            UntypedToken(token)

            # Decode token using settings
            token_backend = TokenBackend(
                algorithm=settings.SIMPLE_JWT['ALGORITHM'],
                signing_key=settings.SIMPLE_JWT['SIGNING_KEY']
            )
            valid_data = token_backend.decode(token, verify=True)

            user_id = int(valid_data.get('user_id'))
            user = User.objects.get(id=user_id)

            if user.is_email_verified:
                return Response({"status": "info", "message": "Email already verified"}, status=status.HTTP_200_OK)

            user.is_email_verified = True
            user.save(update_fields=['is_email_verified'])

            return Response({"status": "success", "message": "Email verified successfully"}, status=status.HTTP_200_OK)

        except (TokenError, InvalidToken, ValueError):
            return Response({"status": "error", "message": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({"status": "error", "message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    # ------------------------
    # "Me" profile
    # ------------------------
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated], url_path='me')
    def me(self, request):
        from rest_framework.serializers import ModelSerializer

        class UserSerializer(ModelSerializer):
            class Meta:
                model = User
                fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_email_verified', 'last_login']

        return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)
