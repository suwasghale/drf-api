# apps/users/api/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.users.api.viewsets import (
    AuthViewSet,
    PasswordViewSet,
    ProfileViewSet,
    AdminUserViewSet,
    SecurityViewSet,
)

router = DefaultRouter()
router.register(r"auth", AuthViewSet, basename="auth")
router.register(r"password", PasswordViewSet, basename="password")
router.register(r"profile", ProfileViewSet, basename="profile")
router.register(r"admin/users", AdminUserViewSet, basename="admin-users")
router.register(r"security", SecurityViewSet, basename="security")

app_name = "users"

urlpatterns = [
    path("", include(router.urls)),
]
