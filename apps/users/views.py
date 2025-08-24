from rest_framework import viewsets, status, throttling
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model, authenticate
from django.urls import reverse
from django.conf import settings
from django.utils import timezone

from rest_framework_simplejwt.tokens import RefreshToken, UntypedToken
from rest_framework_simplejwt.backends import TokenBackend
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

from .serializers import RegisterSerializer, LoginSerializer, UserSerializer
from .utils.email import send_verification_email

User = get_user_model()

class LoginRateThrottle(throttling.UserRateThrottle):
    rate = '5/min'  # 5 login attempts per minute


class EmailVerifyThrottle(throttling.UserRateThrottle):
    rate = '3/min'  # 3 email verifications per minute


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
    @action(detail=False, methods=['get'], url_path='verify-email', permission_classes=[AllowAny], throttle_classes = [EmailVerifyThrottle] )
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
    
    # ---------------- Login ----------------
    @action(detail=False, methods=['post'], url_path='login', permission_classes=[AllowAny], throttle_classes=[LoginRateThrottle])
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        user = authenticate(username=username, password=password)
        if not user:
            return Response({"status": "error", "message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        if not user.is_active:
            return Response({"status": "error", "message": "Account deactivated"}, status=status.HTTP_403_FORBIDDEN)

        refresh = RefreshToken.for_user(user)
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])

        return Response({
            "status": "success",
            "message": "Logged in successfully",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_email_verified": user.is_email_verified,
            },
            "tokens":{
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            }
         
        })


    # ------------------------
    # "Me" profile
    # ------------------------
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        user = request.user
        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_email_verified": user.is_email_verified,
            "last_login": user.last_login
        })
       # ---------------- Logout ----------------
    @action(detail=False, methods=['post'], url_path='logout', permission_classes=[IsAuthenticated])
    def logout(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({"status": "error", "message": "Refresh token required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"status": "success", "message": "Logged out successfully"})
        except Exception:
            return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)

    # ---------------- Deactivate ----------------
    @action(detail=False, methods=['post'], url_path='deactivate', permission_classes=[IsAuthenticated])
    def deactivate(self, request):
        user = request.user
        user.is_active = False
        user.save(update_fields=['is_active'])
        return Response({"status": "success", "message": "Account deactivated"})

    # ---------------- Delete ----------------
    @action(detail=False, methods=['delete'], url_path='delete', permission_classes=[IsAuthenticated])
    def delete_account(self, request):
        user = request.user
        user.delete()
        return Response({"status": "success", "message": "Account deleted"})


    @action(detail=True, methods=['post'], url_path='activate')
    def activate_user(self, request, pk=None):
        user = self.get_object()  # DRF fetches the user with id=pk
        user.is_active = True
        user.save()
        return Response({"status": "success", "message": "User activated"})
