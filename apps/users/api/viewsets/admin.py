# apps/users/api/viewsets/admin.py

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from django.contrib.auth import get_user_model
from apps.users.api.serializers import UserSerializer
from apps.users.utils.audit import log_user_activity

User = get_user_model()


class AdminUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    http_method_names = ["get", "patch", "delete"]

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        user = self.get_object()
        user.is_active = True
        user.is_deleted = False
        user.save()
        log_user_activity(request.user, "admin_activate_user", request=request)
        return Response({"message": "User activated"})
