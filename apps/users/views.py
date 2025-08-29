from django.conf import settings
from django.db import transaction
from django.urls import reverse
from django.core.exceptions import ValidationError as DjangoValidationError

from django.contrib.auth import get_user_model, authenticate, update_session_auth_hash, login
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import PasswordResetTokenGenerator

from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from rest_framework import status, filters, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from rest_framework_simplejwt.tokens import RefreshToken, UntypedToken
from rest_framework_simplejwt.backends import TokenBackend
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.token_blacklist.models import (
    OutstandingToken, 
    BlacklistedToken
    )


from .serializers import (
    RegisterSerializer, 
    LoginSerializer, 
    UserSerializer
)

from .utils.email import (
    send_verification_email,  
    send_password_reset_email 
)

from .utils.audit import log_user_activity

from .utils.password_history import (
    save_password_history, 
    check_password_history
)

User = get_user_model()
token_generator = PasswordResetTokenGenerator()


class UserViewSet(viewsets.ModelViewSet):
    """
    A single controller for users & auth (JWT).
    Features:
    - JWT auth (access + refresh, rotating)
    - Email verification & resend
    - Forgot/reset/change password
    - Throttling per endpoint
    - Account lockout / failed attempts
    - Password history
    - Two-factor authentication (2FA)
    - Social login hooks
    - Audit logs
    - Role-based access
    """
    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["username", "email", "first_name", "last_name"]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    # global throttle class; use per-action scopes
    throttle_classes = [ScopedRateThrottle]

    # -------- permissions per action ----------
    def get_permissions(self):
        # default: admin-only for list/retrieve (safer)
        if self.action in ["list", "retrieve"]:
            return [IsAdminUser()]
        if self.action in [
            "register", "login", "verify_email",
            "resend_verification", "change_password", "forgot_password", "reset_password", "logout", "logout_all"
        ]:
            return [AllowAny()]
        # everything else requires login
        return [IsAuthenticated()]

    # -------- throttling scopes per action ----
    def get_throttles(self):
        scopes = {
            "login": "login",
            "verify_email": "email_verify",
            "resend_verification": "email_verify",
            "forgot_password": "forgot_password",
        }
        for action_name, scope in scopes.items():
            if self.action == action_name:
                # attach scope dynamically
                throttle = ScopedRateThrottle()
                throttle.scope = scope
                return [throttle]
        return super().get_throttles()

    # ===================== AUTH FLOWS =====================

    # -------------------- REGISTER -----------------------------    
    @action(detail=False, methods=["post"], url_path="register")
    def register(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # optional: allow immediate login; keep email verification flag separate
        user.is_active = True
        user.save(update_fields=["is_active"])

        # Issue access token for email verification link
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        verification_url = request.build_absolute_uri(
            reverse("users-verify-email") + f"?token={access_token}"
        )
        send_verification_email(user.email, user.username, verification_url)
        # user log activity
        log_user_activity(user, 'register')

        return Response(
            {"status": "success", "message": "User registered. Check your email to verify."},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["get"], url_path="verify-email")
    def verify_email(self, request):
        token = request.query_params.get("token")
        if not token:
            return Response({"status": "error", "message": "Token missing"}, status=400)

        token = str(token).strip()
        try:
            # Validate signature/expiry
            UntypedToken(token)

            # Decode with your configured algorithm & key
            token_backend = TokenBackend(
                algorithm=settings.SIMPLE_JWT["ALGORITHM"],
                signing_key=settings.SIMPLE_JWT["SIGNING_KEY"],
            )
            payload = token_backend.decode(token, verify=True)
            user_id = int(payload.get("user_id"))

            user = User.objects.get(id=user_id)
            if user.is_email_verified:
                return Response({"status": "info", "message": "Email already verified"})

            user.is_email_verified = True
            user.save(update_fields=["is_email_verified"])
            # user log activity
            log_user_activity(user, 'verify_email')
            
            return Response({"status": "success", "message": "Email verified successfully"})
        except (TokenError, InvalidToken, ValueError, TypeError):
            return Response({"status": "error", "message": "Invalid or expired token"}, status=400)
        except User.DoesNotExist:
            return Response({"status": "error", "message": "User not found"}, status=404)

    @action(detail=False, methods=["post"], url_path="resend-verification")
    def resend_verification(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"status": "error", "message": "Email required"}, status=400)
        try:
            user = User.objects.get(email__iexact=email) # __iexact: case-insensitive comparison
            if user.is_email_verified:
                return Response({"status": "info", "message": "Email already verified"})
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            verification_url = request.build_absolute_uri(
                reverse("users-verify-email") + f"?token={access_token}"
            )
            send_verification_email(user.email, user.username, verification_url)
            # user log activity
            log_user_activity(user, 'resend_verification')

        except User.DoesNotExist:
            pass  # don't leak registered emails
        return Response({"status": "success", "message": "If the email exists, a verification link was sent."})

    @action(detail=False, methods=["post"], url_path="login")
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        identifier = serializer.validated_data["username"]
        password = serializer.validated_data["password"]

        # allow email or username without a custom backend
        user = authenticate(request,username=identifier, password=password)
        attempted_user = None
        if not user:
            # try email → username fallback
            try:
                attempted_user = User.objects.get(email__iexact=identifier)
                user = authenticate(username=attempted_user.username, password=password)
            except User.DoesNotExist:
                attempted_user = None
                user = None

        # Handle failed attempts & lockout
        if user:
            if getattr(user, "failed_login_attempts", 0)>=5:
                return Response({"status":"error","message":"Account locked due to multiple failed attempts"},status=403)
        if not user:
            log_user_activity(
                user=attempted_user,
                action=f"Login failed for identifier '{identifier}'",
                request=request,
                outcome="FAILURE",
                extra_data={"attempted_username": identifier}
            )
            # Optionally increment failed_login_attempts for existing user
            if attempted_user:
                attempted_user.failed_login_attempts = getattr(attempted_user, "failed_login_attempts", 0) + 1
                attempted_user.save(update_fields=["failed_login_attempts"])
                
                # account lockout check
                if attempted_user.failed_login_attempts >=5:
                    log_user_activity(
                        user=user,
                        action="Login attempt blocked due to multiple failed attempts",
                        request=request,
                        outcome="BLOCKED"
                    )
                    return Response({"status": "error", "message": "Account locked due to multiple failed attempts"}, status=status.HTTP_403_FORBIDDEN)
                    
            return Response({"status": "error", "message": "Invalid credentials"}, status=401)

    
        # account deactivated check
        if not user.is_active:
            log_user_activity(
                user=user,
                action="Login attempt blocked: account deactivated",
                request=request,
                outcome="BLOCKED"
            )
            return Response({"status": "error", "message": "Account deactivated"}, status=status.HTTP_403_FORBIDDEN)

        # reset failed login attempts
        user.failed_login_attempts = 0
        user.save(update_fields=["failed_login_attempts"])

        # Triggers user_logged_in signal + updates last_login
        login(request, user)

        # Issue jwt-tokens
        refresh = RefreshToken.for_user(user)
        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        # user log activity
        # log_user_activity(user,"login" )

        return Response({
            "status": "success",
            "message": "Logged in successfully",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_email_verified": user.is_email_verified,
            },
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
        })

    @action(detail=False, methods=["post"], url_path="logout")
    def logout(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"status": "error", "message": "Refresh token required"}, status=400)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()

            # user log activity
            log_user_activity(request.user, "logout" )

            return Response({"status": "success", "message": "Logged out successfully"})
        except Exception as e:
            print("logout error message: ", e)
            return Response({"status": "error", "message": "Invalid token"}, status=400)

    @action(detail=False, methods=["post"], url_path="logout-all")
    def logout_all(self, request):
        """
        Blacklist all outstanding refresh tokens for this user (invalidate every device).
        """
        tokens = OutstandingToken.objects.filter(user=request.user)
        for t in tokens:
            try:
                BlacklistedToken.objects.get_or_create(token=t)
            except Exception:
                pass

        # use log activity
        log_user_activity(request.user, "logout_all")

        return Response({"status": "success", "message": "Logged out from all devices"})

    # ===================== PASSWORD FLOWS =====================

    @action(detail=False, methods=["post"], url_path="forgot-password", permission_classes=[AllowAny])
    def forgot_password(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"status": "error", "message": "Email required"}, status=400)
        try:
            user = User.objects.get(email__iexact=email)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = token_generator.make_token(user)
            reset_url = request.build_absolute_uri(
                reverse("users-reset-password") + f"?uid={uid}&token={token}"
            )
            # send a reset-specific email (subject/body say 'Reset password')
            send_password_reset_email(user.email, user.username, reset_url)

            # user log activity
            log_user_activity(user, 'forgot_password')

        except User.DoesNotExist:
            pass  # don't reveal if user exists / to prevent enumeration
        return Response({"status": "success", "message": "If the email exists, a reset link was sent."})

    @action(detail=False, methods=["post"], url_path="reset-password", url_name="reset-password", permission_classes=[AllowAny])
    def reset_password(self, request):
        # supports both JSON body and query params (for convenience)
        uid = request.data.get("uid") or request.query_params.get("uid")
        token = request.data.get("token") or request.query_params.get("token")
        new_password = request.data.get("new_password")

        if not (uid and token and new_password):
            return Response(
                {"status": "error", "message": "uid, token and new_password all are required"}, status=400
            )

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (User.DoesNotExist, ValueError, TypeError):
            return Response({"status": "error", "message": "Invalid user"}, status=400)
        
        # check password history
        if check_password_history(user, new_password):
            return Response({"status": "error", "message": "You cannot reuse recent passwords"}, status=400)

        if not token_generator.check_token(user, token):
            return Response({"status": "error", "message": "Invalid or expired token"}, status=400)

        # strong password validation
        try:
            validate_password(new_password, user=user)
        except DjangoValidationError as e:
            return Response({"status": "error", "message": e.messages}, status=400)
        
        # Capture the old hashed password before setting the new one
        old_hashed_password = user.password

        try:
            with transaction.atomic(): # ensures that a block of code is executed as a single, indivisible operation
                # Set the new password 
                user.set_password(new_password)
                user.save(update_fields=['password'])
                
                # Save the old password to history
                if old_hashed_password:
                    save_password_history(user, old_hashed_password)
                
                # Optionally update the session to prevent being logged out
                update_session_auth_hash(request, user)

                # user log activity
                log_user_activity(user, 'reset_password')
                return Response({"status": "success", "message": "Password reset successfully."}) 
        except Exception as e:
            return Response({"status": "error", "message": f"An error occurred: {e}"})
        return Response({"status": "success", "message": "Password has been reset successfully."})

    @action(detail=False, methods=["post"], url_path="change-password")
    def change_password(self, request):
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")
        if not (old_password and new_password):
            return Response({"status": "error", "message": "Both old_password and new_password are required"}, status=400)

        user = request.user
        if not user.check_password(old_password):
            return Response({"status": "error", "message": "Old password is incorrect"}, status=400)
        
        # Retrieve the *current* hashed password before it is changed
        current_hashed_password = user.password

        # Check if the new password is the same as the current one
        if user.check_password(new_password):
            return Response({"status": "error", "message": "The new password cannot be the same as the current password"}, status=400)

        # check password history
        if check_password_history(user, new_password):
            return Response({"status": "error", "message": "You cannot reuse recent passwords"}, status=400)

        # strong password validation
        try:
            validate_password(new_password, user=user)
        except DjangoValidationError as e:
            return Response({"status": "error", "message": e.messages}, status=400)


        try:
            with transaction.atomic(): # ensures that a block of code is executed as a single, indivisible operation
                # Set the new password 
                user.set_password(new_password)
                user.save(update_fields=['password'])
                
                # Save the old password to history
                if current_hashed_password:
                    save_password_history(user, current_hashed_password)
                
                # Optionally update the session to prevent being logged out
                update_session_auth_hash(request, user)

                # user log activity
                log_user_activity(user, 'change_password')
                return Response({"status": "success", "message": "Password reset successfully."}) 
        except Exception as e:
            return Response({"status": "error", "message": f"An error occurred: {e}"})

        return Response({"status": "success", "message": "Password changed successfully."})

    # ===================== PROFILE / ACCOUNT =====================

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        data = UserSerializer(request.user).data
        return Response(data)

    @action(detail=False, methods=["patch"], url_path="update-profile")
    def update_profile(self, request):
        # only allow safe profile fields here (no password/flags)
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"status": "success", "message": "Profile updated", "user": serializer.data})

    @action(detail=False, methods=["post"], url_path="deactivate")
    def deactivate(self, request):
        request.user.is_active = False
        request.user.save(update_fields=["is_active"])
        return Response({"status": "success", "message": "Account deactivated"})

    @action(detail=False, methods=["delete"], url_path="delete")
    def delete_account(self, request):
        request.user.delete()
        return Response({"status": "success", "message": "Account deleted"})

    # -------- Admin-only user activation toggle (uses detail route /users/{id}/activate/) ----------
    @action(detail=True, methods=["post"], url_path="activate", permission_classes=[IsAdminUser])
    def activate_user(self, request, pk=None):
        user = self.get_object()
        user.is_active = True
        user.save(update_fields=["is_active"])
        return Response({"status": "success", "message": "User activated"})
    
    # user list
    @action(detail=False, methods=["get"], url_path="list", permission_classes=[IsAdminUser])
    def user_list(self, request):
        users = User.objects.all()
        # Only fields needed for user_list API
        users = User.objects.only('id', 'username', 'email', 'is_email_verified', 'display_name').all()
        serializer = UserSerializer(users, many=True)
        return Response({"status": "success", "users": serializer.data})

