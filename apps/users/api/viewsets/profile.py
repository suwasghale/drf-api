# apps/users/api/viewsets/profile.py

from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.users.api.serializers import UserSerializer, UpdateProfileSerializer
from apps.users.utils.audit import log_user_activity


class ProfileViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def me(self, request):
        return Response(UserSerializer(request.user).data)

    @action(detail=False, methods=["patch"])
    def update(self, request):
        serializer = UpdateProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        log_user_activity(request.user, "update_profile", request=request)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def deactivate(self, request):
        request.user.is_active = False
        request.user.save()
        log_user_activity(request.user, "deactivate_account", request=request)
        return Response({"message": "Account deactivated"})

    @action(detail=False, methods=["delete"])
    def delete(self, request):
        request.user.is_deleted = True
        request.user.deleted_at = timezone.now()
        request.user.is_active = False
        request.user.save()
        log_user_activity(request.user, "delete_account", request=request)
        return Response({"message": "Account deleted"})
