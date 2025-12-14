from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken

from apps.users.utils.audit import log_user_activity

User = get_user_model()


class SecurityViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def sessions(self, request):
        tokens = OutstandingToken.objects.filter(user=request.user)
        return Response([{"id": t.id, "created": t.created_at} for t in tokens])

    @action(detail=False, methods=["post"], permission_classes=[IsAdminUser])
    def unlock_user(self, request):
        user_id = request.data.get("user_id")
        user = User.objects.get(pk=user_id)
        user.failed_login_attempts = 0
        user.is_locked = False
        user.save()
        log_user_activity(request.user, "admin_unlock_user", request=request)
        return Response({"message": "User unlocked"})
