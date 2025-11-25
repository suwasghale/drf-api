from django.conf import settings
from django.db import transaction
from django.urls import reverse
from django.core.exceptions import ValidationError as DjangoValidationError

from django.contrib.auth import get_user_model, authenticate, update_session_auth_hash, login
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import PasswordResetTokenGenerator

from django.contrib.auth.tokens import default_token_generator as token_generator

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


from apps.users.api.serializers import (
    RegisterSerializer, 
    LoginSerializer, 
    UserSerializer
)

from apps.users.utils.email import (
    send_verification_email,  
    send_password_reset_email 
)

from apps.users.utils.audit import log_user_activity

from apps.users.utils.password_history import (
    save_password_history, 
    check_password_history
)

User = get_user_model()
token_generator = PasswordResetTokenGenerator()


# class UserViewSet(viewsets.ModelViewSet):
#     """
#     A single controller for users & auth (JWT).
#     Features:
#     - JWT auth (access + refresh, rotating)
#     - Email verification & resend
#     - Forgot/reset/change password
#     - Throttling per endpoint
#     - Account lockout / failed attempts
#     - Password history
#     - Two-factor authentication (2FA)
#     - Social login hooks
#     - Audit logs
#     - Role-based access
#     - Many more features to be added
#     """
#     queryset = User.objects.all().order_by("-date_joined")
#     serializer_class = UserSerializer
#     filter_backends = [filters.SearchFilter]
#     search_fields = ["username", "email", "first_name", "last_name"]
#     http_method_names = ["get", "post", "patch", "delete", "head", "options"]

#     # global throttle class; use per-action scopes
#     throttle_classes = [ScopedRateThrottle]

#     # -------- permissions per action ----------
#     def get_permissions(self):
#         # default: admin-only for list/retrieve (safer)
#         if self.action in ["list", "retrieve"]:
#             return [IsAdminUser()]
#         if self.action in [
#             "register", "login", "verify_email",
#             "resend_verification", "change_password", "forgot_password", "reset_password", "logout", "logout_all"
#         ]:
#             return [AllowAny()]
#         # everything else requires login
#         return [IsAuthenticated()]

#     # -------- throttling scopes per action ----
#     def get_throttles(self):
#         scopes = {
#             "login": "login",
#             "verify_email": "email_verify",
#             "resend_verification": "email_verify",
#             "forgot_password": "forgot_password",
#             "reset_password": "forgot_password",
#             "change_password": "change_password",
#             "logout": "logout",
#             "logout_all": "logout_all",
#         }
#         for action_name, scope in scopes.items():
#             if self.action == action_name:
#                 # attach scope dynamically
#                 throttle = ScopedRateThrottle()
#                 throttle.scope = scope
#                 return [throttle]
#         return super().get_throttles()

#     # ===================== AUTH FLOWS =====================

#     # -------------------- REGISTER -----------------------------    
#     @action(detail=False, methods=["post"], url_path="register")
#     def register(self, request):
#         serializer = RegisterSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         user = serializer.save()

#         # optional: allow immediate login; keep email verification flag separate
#         user.is_active = True
#         user.save(update_fields=["is_active"])

#         # Issue access token for email verification link
#         refresh = RefreshToken.for_user(user)
#         access_token = str(refresh.access_token)

#         verification_url = request.build_absolute_uri(
#             reverse("users-verify-email") + f"?token={access_token}"
#         )
#         send_verification_email(user.email, user.username, verification_url)
#         # user log activity
#         log_user_activity(user, 'register')

#         return Response(
#             {"status": "success", "message": "User registered. Check your email to verify."},
#             status=status.HTTP_201_CREATED,
#         )

#     @action(detail=False, methods=["get"], url_path="verify-email")
#     def verify_email(self, request):
#         token = request.query_params.get("token")
#         if not token:
#             return Response({"status": "error", "message": "Token missing"}, status=400)

#         token = str(token).strip()
#         try:
#             # Validate signature/expiry
#             UntypedToken(token)

#             # Decode with your configured algorithm & key
#             token_backend = TokenBackend(
#                 algorithm=settings.SIMPLE_JWT["ALGORITHM"],
#                 signing_key=settings.SIMPLE_JWT["SIGNING_KEY"],
#             )
#             payload = token_backend.decode(token, verify=True)
#             user_id = int(payload.get("user_id"))

#             user = User.objects.get(id=user_id)
#             if user.is_email_verified:
#                 return Response({"status": "info", "message": "Email already verified"})

#             user.is_email_verified = True
#             user.save(update_fields=["is_email_verified"])
#             # user log activity
#             log_user_activity(user, 'verify_email')
            
#             return Response({"status": "success", "message": "Email verified successfully"})
#         except (TokenError, InvalidToken, ValueError, TypeError):
#             return Response({"status": "error", "message": "Invalid or expired token"}, status=400)
#         except User.DoesNotExist:
#             return Response({"status": "error", "message": "User not found"}, status=404)

#     @action(detail=False, methods=["post"], url_path="resend-verification")
#     def resend_verification(self, request):
#         email = request.data.get("email")
#         if not email:
#             return Response({"status": "error", "message": "Email required"}, status=400)
#         try:
#             user = User.objects.get(email__iexact=email) # __iexact: case-insensitive comparison
#             if user.is_email_verified:
#                 return Response({"status": "info", "message": "Email already verified"})
#             refresh = RefreshToken.for_user(user)
#             access_token = str(refresh.access_token)
#             verification_url = request.build_absolute_uri(
#                 reverse("users-verify-email") + f"?token={access_token}"
#             )
#             send_verification_email(user.email, user.username, verification_url)
#             # user log activity
#             log_user_activity(user, 'resend_verification')

#         except User.DoesNotExist:
#             pass  # don't leak registered emails
#         return Response({"status": "success", "message": "If the email exists, a verification link was sent."})

#     @action(detail=False, methods=["post"], url_path="login")
#     def login(self, request):
#         serializer = LoginSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         identifier = serializer.validated_data["username"]
#         password = serializer.validated_data["password"]

#         # allow email or username without a custom backend
#         user = authenticate(request,username=identifier, password=password)
#         attempted_user = None
#         if not user:
#             # try email → username fallback
#             try:
#                 attempted_user = User.objects.get(email__iexact=identifier)
#                 user = authenticate(username=attempted_user.username, password=password)
#             except User.DoesNotExist:
#                 attempted_user = None
#                 user = None

#         # Handle failed attempts & lockout
#         if user:
#             if getattr(user, "failed_login_attempts", 0)>=5:
#                 return Response({"status":"error","message":"Account locked due to multiple failed attempts"},status=403)
#         if not user:
#             log_user_activity(
#                 user=attempted_user,
#                 action=f"Login failed for identifier '{identifier}'",
#                 request=request,
#                 outcome="FAILURE",
#                 extra_data={"attempted_username": identifier}
#             )
#             # Optionally increment failed_login_attempts for existing user
#             if attempted_user:
#                 attempted_user.failed_login_attempts = getattr(attempted_user, "failed_login_attempts", 0) + 1
#                 attempted_user.save(update_fields=["failed_login_attempts"])
                
#                 # account lockout check
#                 if attempted_user.failed_login_attempts >=5:
#                     log_user_activity(
#                         user=user,
#                         action="Login attempt blocked due to multiple failed attempts",
#                         request=request,
#                         outcome="BLOCKED"
#                     )
#                     return Response({"status": "error", "message": "Account locked due to multiple failed attempts"}, status=status.HTTP_403_FORBIDDEN)
                    
#             return Response({"status": "error", "message": "Invalid credentials"}, status=401)

    
#         # account deactivated check
#         if not user.is_active:
#             log_user_activity(
#                 user=user,
#                 action="Login attempt blocked: account deactivated",
#                 request=request,
#                 outcome="BLOCKED"
#             )
#             return Response({"status": "error", "message": "Account deactivated"}, status=status.HTTP_403_FORBIDDEN)

#         # reset failed login attempts
#         user.failed_login_attempts = 0
#         user.save(update_fields=["failed_login_attempts"])

#         # Triggers user_logged_in signal + updates last_login
#         login(request, user)

#         # Issue jwt-tokens
#         refresh = RefreshToken.for_user(user)
#         user.last_login = timezone.now()
#         user.save(update_fields=["last_login"])

#         # user log activity
#         # log_user_activity(user,"login" )

#         return Response({
#             "status": "success",
#             "message": "Logged in successfully",
#             "user": {
#                 "id": user.id,
#                 "username": user.username,
#                 "email": user.email,
#                 "is_email_verified": user.is_email_verified,
#             },
#             "tokens": {
#                 "access": str(refresh.access_token),
#                 "refresh": str(refresh),
#             },
#         })

#     @action(detail=False, methods=["post"], url_path="logout")
#     def logout(self, request):
#         refresh_token = request.data.get("refresh")
#         if not refresh_token:
#             return Response({"status": "error", "message": "Refresh token required"}, status=400)
#         try:
#             token = RefreshToken(refresh_token)
#             token.blacklist()

#             # user log activity
#             log_user_activity(request.user, "logout" )

#             return Response({"status": "success", "message": "Logged out successfully"})
#         except Exception as e:
#             print("logout error message: ", e)
#             return Response({"status": "error", "message": "Invalid token"}, status=400)

#     @action(detail=False, methods=["post"], url_path="logout-all")
#     def logout_all(self, request):
#         """
#         Blacklist all outstanding refresh tokens for this user (invalidate every device).
#         """
#         tokens = OutstandingToken.objects.filter(user=request.user)
#         for t in tokens:
#             try:
#                 BlacklistedToken.objects.get_or_create(token=t)
#             except Exception:
#                 pass

#         # use log activity
#         log_user_activity(request.user, "logout_all")

#         return Response({"status": "success", "message": "Logged out from all devices"})

#     # ===================== PASSWORD FLOWS =====================

#     @action(detail=False, methods=["post"], url_path="forgot-password", permission_classes=[AllowAny])
#     def forgot_password(self, request):
#         email = request.data.get("email")
#         if not email:
#             return Response({"status": "error", "message": "Email required"}, status=400)
#         try:
#             user = User.objects.get(email__iexact=email)
#             uid = urlsafe_base64_encode(force_bytes(user.pk))
#             token = token_generator.make_token(user)
#             reset_url = request.build_absolute_uri(
#                 reverse("users-reset-password") + f"?uid={uid}&token={token}"
#             )
#             # send a reset-specific email (subject/body say 'Reset password')
#             send_password_reset_email(user.email, user.username, reset_url)

#             # user log activity
#             log_user_activity(user, 'forgot_password')

#         except User.DoesNotExist:
#             pass  # don't reveal if user exists / to prevent enumeration
#         return Response({"status": "success", "message": "If the email exists, a reset link was sent."})

#     @action(detail=False, methods=["post"], url_path="reset-password", url_name="reset-password", permission_classes=[AllowAny])
#     def reset_password(self, request):
#         # supports both JSON body and query params (for convenience)
#         uid = request.data.get("uid") or request.query_params.get("uid")
#         token = request.data.get("token") or request.query_params.get("token")
#         new_password = request.data.get("new_password")

#         if not (uid and token and new_password):
#             return Response(
#                 {"status": "error", "message": "uid, token and new_password all are required"}, status=400
#             )

#         try:
#             user_id = force_str(urlsafe_base64_decode(uid))
#             user = User.objects.get(pk=user_id)
#         except (User.DoesNotExist, ValueError, TypeError):
#             return Response({"status": "error", "message": "Invalid user"}, status=400)
        
#         # check password history
#         if check_password_history(user, new_password):
#             return Response({"status": "error", "message": "You cannot reuse recent passwords"}, status=400)

#         if not token_generator.check_token(user, token):
#             return Response({"status": "error", "message": "Invalid or expired token"}, status=400)

#         # strong password validation
#         try:
#             validate_password(new_password, user=user)
#         except DjangoValidationError as e:
#             return Response({"status": "error", "message": e.messages}, status=400)
        
#         # Capture the old hashed password before setting the new one
#         old_hashed_password = user.password

#         try:
#             with transaction.atomic(): # ensures that a block of code is executed as a single, indivisible operation
#                 # Set the new password 
#                 user.set_password(new_password)
#                 user.save(update_fields=['password'])
                
#                 # Save the old password to history
#                 if old_hashed_password:
#                     save_password_history(user, old_hashed_password)
                
#                 # Optionally update the session to prevent being logged out
#                 update_session_auth_hash(request, user)

#                 # user log activity
#                 log_user_activity(user, 'reset_password')
#                 return Response({"status": "success", "message": "Password reset successfully."}) 
#         except Exception as e:
#             return Response({"status": "error", "message": f"An error occurred: {e}"})
#         return Response({"status": "success", "message": "Password has been reset successfully."})

#     @action(detail=False, methods=["post"], url_path="change-password")
#     def change_password(self, request):
#         old_password = request.data.get("old_password")
#         new_password = request.data.get("new_password")
#         if not (old_password and new_password):
#             return Response({"status": "error", "message": "Both old_password and new_password are required"}, status=400)

#         user = request.user
#         if not user.check_password(old_password):
#             return Response({"status": "error", "message": "Old password is incorrect"}, status=400)
        
#         # Retrieve the *current* hashed password before it is changed
#         current_hashed_password = user.password

#         # Check if the new password is the same as the current one
#         if user.check_password(new_password):
#             return Response({"status": "error", "message": "The new password cannot be the same as the current password"}, status=400)

#         # check password history
#         if check_password_history(user, new_password):
#             return Response({"status": "error", "message": "You cannot reuse recent passwords"}, status=400)

#         # strong password validation
#         try:
#             validate_password(new_password, user=user)
#         except DjangoValidationError as e:
#             return Response({"status": "error", "message": e.messages}, status=400)


#         try:
#             with transaction.atomic(): # ensures that a block of code is executed as a single, indivisible operation
#                 # Set the new password 
#                 user.set_password(new_password)
#                 user.save(update_fields=['password'])
                
#                 # Save the old password to history
#                 if current_hashed_password:
#                     save_password_history(user, current_hashed_password)
                
#                 # Optionally update the session to prevent being logged out
#                 update_session_auth_hash(request, user)

#                 # user log activity
#                 log_user_activity(user, 'change_password')
#                 return Response({"status": "success", "message": "Password reset successfully."}) 
#         except Exception as e:
#             return Response({"status": "error", "message": f"An error occurred: {e}"})

#         return Response({"status": "success", "message": "Password changed successfully."})

#     # ===================== PROFILE / ACCOUNT =====================

#     @action(detail=False, methods=["get"], url_path="me")
#     def me(self, request):
#         data = UserSerializer(request.user).data
#         return Response(data)

#     @action(detail=False, methods=["patch"], url_path="update-profile")
#     def update_profile(self, request):
#         # only allow safe profile fields here (no password/flags)
#         serializer = UserSerializer(request.user, data=request.data, partial=True)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response({"status": "success", "message": "Profile updated", "user": serializer.data})

#     @action(detail=False, methods=["post"], url_path="deactivate")
#     def deactivate(self, request):
#         request.user.is_active = False
#         request.user.save(update_fields=["is_active"])
#         return Response({"status": "success", "message": "Account deactivated"})

#     @action(detail=False, methods=["delete"], url_path="delete")
#     def delete_account(self, request):
#         request.user.delete()
#         return Response({"status": "success", "message": "Account deleted"})

#     # -------- Admin-only user activation toggle (uses detail route /users/{id}/activate/) ----------
#     @action(detail=True, methods=["post"], url_path="activate", permission_classes=[IsAdminUser])
#     def activate_user(self, request, pk=None):
#         user = self.get_object()
#         user.is_active = True
#         user.save(update_fields=["is_active"])
#         return Response({"status": "success", "message": "User activated"})
    
#     # user list
#     @action(detail=False, methods=["get"], url_path="list", permission_classes=[IsAdminUser])
#     def user_list(self, request):
#         users = User.objects.all()
#         # Only fields needed for user_list API
#         users = User.objects.only('id', 'username', 'email', 'is_email_verified', 'display_name').all()
#         serializer = UserSerializer(users, many=True)
#         return Response({"status": "success", "users": serializer.data})


# # -----------------------------
# # AdminUserViewSet: admin-only operations
# # -----------------------------
# class AdminUserViewSet(viewsets.ModelViewSet):
#     """
#     Admin operations for user management.
#     """
#     queryset = User.objects.all().order_by("-date_joined")
#     serializer_class = UserSerializer
#     permission_classes = [IsAdminUser]
#     http_method_names = ["get", "post", "patch", "delete", "head", "options"]

#     @action(detail=True, methods=["post"], url_path="activate", permission_classes=[IsAdminUser])
#     def activate_user(self, request, pk=None):
#         user = self.get_object()
#         user.is_active = True
#         user.is_deleted = False
#         user.deleted_at = None
#         user.save(update_fields=["is_active", "is_deleted", "deleted_at"])
#         log_user_activity(request.user, "admin_activate_user", request=request, extra_data={"target_user": user.id})
#         return Response({"status": "success", "message": "User activated"})

#     @action(detail=False, methods=["get"], url_path="list-users", permission_classes=[IsAdminUser])
#     def list_users(self, request):
#         users = User.objects.only('id', 'username', 'email', 'is_email_verified', 'display_name').all()
#         serializer = UserSerializer(users, many=True)
#         return Response({"status": "success", "users": serializer.data})


# # -----------------------------
# # SecurityViewSet: session/device listing, lock/unlock utilities (optional)
# # -----------------------------
# class SecurityViewSet(viewsets.GenericViewSet):
#     permission_classes = [IsAuthenticated]

#     @action(detail=False, methods=["get"], url_path="sessions")
#     def list_sessions(self, request):
#         # OPTIONAL: requires tracking sessions/outstanding tokens
#         tokens = OutstandingToken.objects.filter(user=request.user)
#         token_info = [{"id": str(t.id), "created": t.created_at} for t in tokens]
#         return Response({"status": "success", "sessions": token_info})

#     @action(detail=False, methods=["post"], url_path="unlock-user", permission_classes=[IsAdminUser])
#     def unlock_user(self, request):
#         user_id = request.data.get("user_id")
#         if not user_id:
#             return Response({"status": "error", "message": "user_id required"}, status=status.HTTP_400_BAD_REQUEST)
#         try:
#             user = User.objects.get(pk=user_id)
#             user.is_locked = False
#             user.failed_login_attempts = 0
#             user.lock_expires_at = None
#             user.save(update_fields=["is_locked", "failed_login_attempts", "lock_expires_at"])
#             log_user_activity(request.user, "admin_unlock_user", request=request, extra_data={"target_user": user.id})
#             return Response({"status": "success", "message": "User unlocked"})
#         except User.DoesNotExist:
#             return Response({"status": "error", "message": "User not found"}, status=status.HTTP_404_NOT_FOUND)


from django.conf import settings
from django.db import transaction
from django.urls import reverse
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth import get_user_model, authenticate, update_session_auth_hash, login, logout
from django.contrib.auth.tokens import default_token_generator as token_generator
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
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

from apps.users.api.serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
    ChangePasswordSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    UpdateProfileSerializer,
)
from apps.users.utils.email import send_verification_email, send_password_reset_email
from apps.users.utils.audit import log_user_activity
from apps.users.utils.password_history import save_password_history, check_password_history

User = get_user_model()

# -----------------------------
# AuthViewSet: register, email verify, login, logout, password flows
# -----------------------------
class AuthViewSet(viewsets.GenericViewSet):
    """
    Authentication endpoints: register, verify-email, resend-verification,
    login, logout, forgot-password, reset-password, change-password.
    """
    serializer_class = UserSerializer
    throttle_classes = [ScopedRateThrottle]
    permission_classes = [AllowAny]  # overridden per-action where required

    # action -> throttle scope mapping
    throttle_scopes = {
        "login": "login",
        "verify_email": "email_verify",
        "resend_verification": "email_verify",
        "forgot_password": "forgot_password",
        "reset_password": "forgot_password",
        "change_password": "change_password",
        "logout": "logout",
        "logout_all": "logout_all",
    }

    def get_throttles(self):
        if hasattr(self, "action") and self.action in self.throttle_scopes:
            throttle = ScopedRateThrottle()
            throttle.scope = self.throttle_scopes[self.action]
            return [throttle]
        return super().get_throttles()

    # ---------- Register ----------
    @action(detail=False, methods=["post"], url_path="register", permission_classes=[AllowAny])
    def register(self, request):
        """
        Creates the user (is_active default can remain False if you want email verification gating).
        Creates initial password history entry and sends a one-time verification token (uid+token).
        """
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            user = serializer.save()
            # optionally keep is_active False until verification; current original code set True
            # Ensure email verification flow uses uid+token (safer than exposing a JWT)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = token_generator.make_token(user)
            verification_url = request.build_absolute_uri(
                reverse("users:verify-email") + f"?uid={uid}&token={token}"
            )
            send_verification_email(user.email, user.username, verification_url)
            # Save initial password hash into history if RegisterSerializer saved a raw password (it shouldn't)
            # But ensure password history exists for compliance
            # log activity
            log_user_activity(user, "register", request=request, outcome="SUCCESS")

        return Response({"status": "success", "message": "User registered. Check your email to verify."},
                        status=status.HTTP_201_CREATED)

    # ---------- Verify Email ----------
    @action(detail=False, methods=["get"], url_path="verify-email", permission_classes=[AllowAny])
    def verify_email(self, request):
        uid = request.query_params.get("uid")
        token = request.query_params.get("token")
        if not (uid and token):
            return Response({"status": "error", "message": "uid and token required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (ValueError, User.DoesNotExist):
            return Response({"status": "error", "message": "Invalid uid"}, status=status.HTTP_400_BAD_REQUEST)

        if token_generator.check_token(user, token):
            if not user.is_email_verified:
                user.is_email_verified = True
                user.save(update_fields=["is_email_verified"])
                log_user_activity(user, "verify_email", request=request, outcome="SUCCESS")
                return Response({"status": "success", "message": "Email verified successfully"})
            else:
                return Response({"status": "info", "message": "Email already verified"})
        return Response({"status": "error", "message": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)

    # ---------- Resend Verification ----------
    @action(detail=False, methods=["post"], url_path="resend-verification", permission_classes=[AllowAny])
    def resend_verification(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)  # reusing simple email-only serializer
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        try:
            user = User.objects.get(email__iexact=email)
            if user.is_email_verified:
                return Response({"status": "info", "message": "Email already verified"})
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = token_generator.make_token(user)
            verification_url = request.build_absolute_uri(
                reverse("users:verify-email") + f"?uid={uid}&token={token}"
            )
            send_verification_email(user.email, user.username, verification_url)
            log_user_activity(user, "resend_verification", request=request, outcome="SUCCESS")
        except User.DoesNotExist:
            # Do not leak existence
            pass
        return Response({"status": "success", "message": "If the email exists, a verification link was sent."})

    # ---------- Login ----------
    @action(detail=False, methods=["post"], url_path="login", permission_classes=[AllowAny])
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        identifier = serializer.validated_data.get("identifier")
        password = serializer.validated_data.get("password")

        # Try authenticate with identifier as username first, then as email (fallback)
        user = authenticate(request, username=identifier, password=password)
        attempted_user = None
        if user is None:
            # fallback attempt by email
            try:
                attempted_user = User.objects.get(email__iexact=identifier)
                user = authenticate(request, username=attempted_user.username, password=password)
            except User.DoesNotExist:
                attempted_user = None
                user = None

        # If we have an attempted_user, check lock status before proceeding
        if attempted_user:
            if attempted_user.is_locked:
                # check expiry
                if attempted_user.lock_expires_at and attempted_user.lock_expires_at > timezone.now():
                    log_user_activity(attempted_user, "login_blocked_locked", request=request, outcome="BLOCKED")
                    return Response({"status": "error", "message": "Account locked due to multiple failed attempts"},
                                    status=status.HTTP_403_FORBIDDEN)
                # unlock if expired
                attempted_user.is_locked = False
                attempted_user.failed_login_attempts = 0
                attempted_user.lock_expires_at = None
                attempted_user.save(update_fields=["is_locked", "failed_login_attempts", "lock_expires_at"])

        if user is None:
            # log failed attempt and increment counter if attempted_user exists
            log_user_activity(attempted_user, f"login_failed_{identifier}", request=request, outcome="FAILURE")
            if attempted_user:
                attempted_user.failed_login_attempts = getattr(attempted_user, "failed_login_attempts", 0) + 1
                attempted_user.last_failed_login_attempt = timezone.now()
                # lock when threshold reached
                if attempted_user.failed_login_attempts >= 5:
                    attempted_user.is_locked = True
                    attempted_user.lock_expires_at = timezone.now() + timezone.timedelta(minutes=15)  # configurable
                attempted_user.save(update_fields=["failed_login_attempts", "last_failed_login_attempt", "is_locked", "lock_expires_at"])
            return Response({"status": "error", "message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        # user authenticated => additional checks
        if not user.is_active or user.is_deleted:
            log_user_activity(user, "login_blocked_inactive_or_deleted", request=request, outcome="BLOCKED")
            return Response({"status": "error", "message": "Account not active"}, status=status.HTTP_403_FORBIDDEN)

        # reset failed attempts on success
        if user.failed_login_attempts:
            user.failed_login_attempts = 0
            user.last_failed_login_attempt = None
            user.is_locked = False
            user.lock_expires_at = None
            user.save(update_fields=["failed_login_attempts", "last_failed_login_attempt", "is_locked", "lock_expires_at"])

        # perform Django login (updates last_login via signal)
        login(request, user)
        refresh = RefreshToken.for_user(user)
        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        # Log user activity with meta info
        log_user_activity(user, "login", request=request, outcome="SUCCESS", extra_data={
            "ip": request.META.get("REMOTE_ADDR"),
            "user_agent": request.META.get("HTTP_USER_AGENT"),
        })

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
            }
        })

    # ---------- Logout ----------
    @action(detail=False, methods=["post"], url_path="logout", permission_classes=[IsAuthenticated])
    def logout(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"status": "error", "message": "Refresh token required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            log_user_activity(request.user, "logout", request=request, outcome="SUCCESS")
            # also log Django logout
            logout(request)
            return Response({"status": "success", "message": "Logged out successfully"})
        except Exception:
            return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)

    # ---------- Logout all ----------
    @action(detail=False, methods=["post"], url_path="logout-all", permission_classes=[IsAuthenticated])
    def logout_all(self, request):
        tokens = OutstandingToken.objects.filter(user=request.user)
        for t in tokens:
            try:
                BlacklistedToken.objects.get_or_create(token=t)
            except Exception:
                pass
        log_user_activity(request.user, "logout_all", request=request, outcome="SUCCESS")
        logout(request)
        return Response({"status": "success", "message": "Logged out from all devices"})

    # ---------- Forgot password (request) ----------
    @action(detail=False, methods=["post"], url_path="forgot-password", permission_classes=[AllowAny])
    def forgot_password(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        try:
            user = User.objects.get(email__iexact=email)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = token_generator.make_token(user)
            reset_url = request.build_absolute_uri(reverse("users:reset-password") + f"?uid={uid}&token={token}")
            send_password_reset_email(user.email, user.username, reset_url)
            log_user_activity(user, "forgot_password", request=request, outcome="SUCCESS")
        except User.DoesNotExist:
            pass
        return Response({"status": "success", "message": "If the email exists, a reset link was sent."})

    # ---------- Reset password (confirm) ----------
    @action(detail=False, methods=["post"], url_path="reset-password", permission_classes=[AllowAny])
    def reset_password(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        uid = serializer.validated_data["uid"]
        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (User.DoesNotExist, ValueError, TypeError):
            return Response({"status": "error", "message": "Invalid user"}, status=status.HTTP_400_BAD_REQUEST)

        if not token_generator.check_token(user, token):
            return Response({"status": "error", "message": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)

        # password history check
        if check_password_history(user, new_password):
            return Response({"status": "error", "message": "You cannot reuse recent passwords"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_password(new_password, user=user)
        except DjangoValidationError as e:
            return Response({"status": "error", "message": e.messages}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                old_hashed = user.password
                user.set_password(new_password)
                user.save(update_fields=["password"])
                if old_hashed:
                    save_password_history(user, old_hashed)
                log_user_activity(user, "reset_password", request=request, outcome="SUCCESS")
                return Response({"status": "success", "message": "Password reset successfully."})
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ---------- Change password (authenticated) ----------
    @action(detail=False, methods=["post"], url_path="change-password", permission_classes=[IsAuthenticated])
    def change_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        old_password = serializer.validated_data["old_password"]
        new_password = serializer.validated_data["new_password"]
        user = request.user

        if not user.check_password(old_password):
            log_user_activity(user, "change_password_failed", request=request, outcome="FAILURE")
            return Response({"status": "error", "message": "Old password is incorrect"}, status=status.HTTP_400_BAD_REQUEST)

        if user.check_password(new_password):
            return Response({"status": "error", "message": "The new password cannot be the same as the current password"},
                            status=status.HTTP_400_BAD_REQUEST)

        if check_password_history(user, new_password):
            return Response({"status": "error", "message": "You cannot reuse recent passwords"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_password(new_password, user=user)
        except DjangoValidationError as e:
            return Response({"status": "error", "message": e.messages}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                current_hashed = user.password
                user.set_password(new_password)
                user.save(update_fields=["password"])
                if current_hashed:
                    save_password_history(user, current_hashed)
                update_session_auth_hash(request, user)  # optional for session-based
                log_user_activity(user, "change_password", request=request, outcome="SUCCESS")
                return Response({"status": "success", "message": "Password changed successfully."})
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# -----------------------------
# ProfileViewSet: me, update-profile, deactivate, delete (soft-delete)
# -----------------------------
class ProfileViewSet(viewsets.GenericViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="me", permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=["patch"], url_path="update-profile", permission_classes=[IsAuthenticated])
    def update_profile(self, request):
        serializer = UpdateProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        log_user_activity(request.user, "update_profile", request=request, outcome="SUCCESS")
        return Response({"status": "success", "message": "Profile updated", "user": serializer.data})

    @action(detail=False, methods=["post"], url_path="deactivate", permission_classes=[IsAuthenticated])
    def deactivate(self, request):
        request.user.is_active = False
        request.user.save(update_fields=["is_active"])
        log_user_activity(request.user, "deactivate_account", request=request, outcome="SUCCESS")
        return Response({"status": "success", "message": "Account deactivated"})

    @action(detail=False, methods=["delete"], url_path="delete", permission_classes=[IsAuthenticated])
    def delete_account(self, request):
        # perform soft delete (model supports is_deleted/deleted_at)
        request.user.is_deleted = True
        request.user.deleted_at = timezone.now()
        request.user.is_active = False
        request.user.save(update_fields=["is_deleted", "deleted_at", "is_active"])
        log_user_activity(request.user, "delete_account", request=request, outcome="SUCCESS")
        return Response({"status": "success", "message": "Account marked as deleted (soft delete)"})

# -----------------------------
# AdminUserViewSet: admin-only operations
# -----------------------------
class AdminUserViewSet(viewsets.ModelViewSet):
    """
    Admin operations for user management.
    """
    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    @action(detail=True, methods=["post"], url_path="activate", permission_classes=[IsAdminUser])
    def activate_user(self, request, pk=None):
        user = self.get_object()
        user.is_active = True
        user.is_deleted = False
        user.deleted_at = None
        user.save(update_fields=["is_active", "is_deleted", "deleted_at"])
        log_user_activity(request.user, "admin_activate_user", request=request, extra_data={"target_user": user.id})
        return Response({"status": "success", "message": "User activated"})

    @action(detail=False, methods=["get"], url_path="list-users", permission_classes=[IsAdminUser])
    def list_users(self, request):
        users = User.objects.only('id', 'username', 'email', 'is_email_verified', 'display_name').all()
        serializer = UserSerializer(users, many=True)
        return Response({"status": "success", "users": serializer.data})

# -----------------------------
# SecurityViewSet: session/device listing, lock/unlock utilities (optional)
# -----------------------------
class SecurityViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="sessions")
    def list_sessions(self, request):
        # OPTIONAL: requires tracking sessions/outstanding tokens
        tokens = OutstandingToken.objects.filter(user=request.user)
        token_info = [{"id": str(t.id), "created": t.created_at} for t in tokens]
        return Response({"status": "success", "sessions": token_info})

    @action(detail=False, methods=["post"], url_path="unlock-user", permission_classes=[IsAdminUser])
    def unlock_user(self, request):
        user_id = request.data.get("user_id")
        if not user_id:
            return Response({"status": "error", "message": "user_id required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(pk=user_id)
            user.is_locked = False
            user.failed_login_attempts = 0
            user.lock_expires_at = None
            user.save(update_fields=["is_locked", "failed_login_attempts", "lock_expires_at"])
            log_user_activity(request.user, "admin_unlock_user", request=request, extra_data={"target_user": user.id})
            return Response({"status": "success", "message": "User unlocked"})
        except User.DoesNotExist:
            return Response({"status": "error", "message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
