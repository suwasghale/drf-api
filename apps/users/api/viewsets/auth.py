from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.tokens import default_token_generator

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

from apps.users.api.serializers import RegisterSerializer, LoginSerializer
from apps.users.utils.email import send_verification_email
from apps.users.utils.audit import log_user_activity

User = get_user_model()
token_generator = default_token_generator


class AuthViewSet(viewsets.GenericViewSet):
    """
    Authentication endpoints:
    - register
    - verify email
    - resend verification
    - login
    - logout / logout-all
    """

    throttle_classes = [ScopedRateThrottle]
    permission_classes = [AllowAny]

    throttle_scopes = {
        "login": "login",
        "register": "register",
        "verify_email": "email_verify",
        "resend_verification": "email_verify",
        "logout": "logout",
        "logout_all": "logout_all",
    }

    def get_throttles(self):
        if self.action in self.throttle_scopes:
            throttle = ScopedRateThrottle()
            throttle.scope = self.throttle_scopes[self.action]
            return [throttle]
        return super().get_throttles()

    # ---------- Register ----------
    @action(detail=False, methods=["post"])
    def register(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = token_generator.make_token(user)

        verification_url = request.build_absolute_uri(
            reverse("users:verify-email") + f"?uid={uid}&token={token}"
        )
        send_verification_email(user.email, user.username, verification_url)
        log_user_activity(user, "register", request=request)

        return Response(
            {"status": "success", "message": "User registered. Verify email."},
            status=status.HTTP_201_CREATED,
        )

    # ---------- Verify email ----------
    @action(detail=False, methods=["get"], url_path="verify-email")
    def verify_email(self, request):
        uid = request.query_params.get("uid")
        token = request.query_params.get("token")

        if not uid or not token:
            return Response({"message": "uid and token required"}, status=400)

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except Exception:
            return Response({"message": "Invalid uid"}, status=400)

        if token_generator.check_token(user, token):
            user.is_email_verified = True
            user.save(update_fields=["is_email_verified"])
            log_user_activity(user, "verify_email", request=request)
            return Response({"message": "Email verified"})

        return Response({"message": "Invalid or expired token"}, status=400)

    # ---------- Resend verification ----------
    @action(detail=False, methods=["post"], url_path="resend-verification")
    def resend_verification(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"message": "Email required"}, status=400)

        try:
            user = User.objects.get(email__iexact=email)
            if user.is_email_verified:
                return Response({"message": "Already verified"})

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = token_generator.make_token(user)
            verification_url = request.build_absolute_uri(
                reverse("users:verify-email") + f"?uid={uid}&token={token}"
            )
            send_verification_email(user.email, user.username, verification_url)
            log_user_activity(user, "resend_verification", request=request)
        except User.DoesNotExist:
            pass

        return Response({"message": "If email exists, verification sent"})

    # ---------- Login ----------
    @action(detail=False, methods=["post"])
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        identifier = serializer.validated_data["identifier"]
        password = serializer.validated_data["password"]

        user = authenticate(request, username=identifier, password=password)

        if not user:
            return Response({"message": "Invalid credentials"}, status=401)

        if not user.is_active or not user.is_email_verified:
            return Response({"message": "Account inactive or unverified"}, status=403)

        login(request, user)
        refresh = RefreshToken.for_user(user)
        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        log_user_activity(user, "login", request=request)

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        })

    # ---------- Logout ----------
    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def logout(self, request):
        refresh = request.data.get("refresh")
        if not refresh:
            return Response({"message": "Refresh token required"}, status=400)

        token = RefreshToken(refresh)
        token.blacklist()
        logout(request)
        log_user_activity(request.user, "logout", request=request)

        return Response({"message": "Logged out"})

    # ---------- Logout all ----------
    @action(detail=False, methods=["post"], url_path="logout-all", permission_classes=[IsAuthenticated])
    def logout_all(self, request):
        for token in OutstandingToken.objects.filter(user=request.user):
            BlacklistedToken.objects.get_or_create(token=token)

        logout(request)
        log_user_activity(request.user, "logout_all", request=request)
        return Response({"message": "Logged out everywhere"})
