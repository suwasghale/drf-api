from django.db import transaction
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.users.api.serializers import (
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    ChangePasswordSerializer,
)
from apps.users.utils.email import send_password_reset_email
from apps.users.utils.password_history import check_password_history, save_password_history
from apps.users.utils.audit import log_user_activity

User = get_user_model()
token_generator = default_token_generator


class PasswordViewSet(viewsets.GenericViewSet):

    # ---------- Forgot ----------
    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def forgot(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        try:
            user = User.objects.get(email__iexact=email)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = token_generator.make_token(user)
            send_password_reset_email(user.email, user.username, uid, token)
            log_user_activity(user, "forgot_password", request=request)
        except User.DoesNotExist:
            pass

        return Response({"message": "If email exists, reset sent"})

    # ---------- Reset ----------
    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def reset(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uid = serializer.validated_data["uid"]
        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]

        user = User.objects.get(pk=force_str(urlsafe_base64_decode(uid)))

        if not token_generator.check_token(user, token):
            return Response({"message": "Invalid token"}, status=400)

        if check_password_history(user, new_password):
            return Response({"message": "Password reuse not allowed"}, status=400)

        with transaction.atomic():
            old_hash = user.password
            user.set_password(new_password)
            user.save()
            save_password_history(user, old_hash)

        log_user_activity(user, "reset_password", request=request)
        return Response({"message": "Password reset successful"})

    # ---------- Change ----------
    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def change(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"user": request.user})
        serializer.is_valid(raise_exception=True)

        user = request.user
        old = serializer.validated_data["old_password"]
        new = serializer.validated_data["new_password"]

        if not user.check_password(old):
            return Response({"message": "Incorrect old password"}, status=400)

        if check_password_history(user, new):
            return Response({"message": "Password reuse not allowed"}, status=400)

        with transaction.atomic():
            old_hash = user.password
            user.set_password(new)
            user.save()
            save_password_history(user, old_hash)
            update_session_auth_hash(request, user)

        log_user_activity(user, "change_password", request=request)
        return Response({"message": "Password changed"})
