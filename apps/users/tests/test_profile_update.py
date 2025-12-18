from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class UserProfileUpdateAPITestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="TestPass123!"
        )
        self.url = reverse("profile-update-profile")  # adjust if needed

    def authenticate(self):
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}"
        )

    def test_authentication_required(self):
        response = self.client.patch(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_can_update_allowed_fields(self):
        self.authenticate()
        payload = {
            "first_name": "Suwas",
            "last_name": "Ghale",
            "display_name": "Suwas Dev"
        }
        response = self.client.patch(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Suwas")
        self.assertEqual(self.user.display_name, "Suwas Dev")

    def test_user_cannot_update_protected_fields(self):
        self.authenticate()
        payload = {
            "username": "hacked",
            "role": "admin",
            "is_staff": True,
            "is_superuser": True
        }
        response = self.client.patch(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        self.assertNotEqual(self.user.username, "hacked")
        self.assertFalse(self.user.is_staff)
