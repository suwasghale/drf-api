from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class UserMeAPITestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@testuser.com",
            password="TestPass123!"
        )

        self.me_url = reverse("profile-me")

    def authenticate(self, user):
        """Helper method to authenticate using JWT"""
        refresh = RefreshToken.for_user(user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}"
        )

    def test_me_requires_authentication(self):
        """Ensure /me cannot be accessed without authentication"""
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_returns_authenticated_user_data(self):
        """Authenticated user should get correct data"""
        self.authenticate(self.user)
        response = self.client.get(self.me_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        self.assertEqual(data["username"], self.user.username)
        self.assertEqual(data["email"], self.user.email)

        # Security assertions
        self.assertNotIn("password", data)
        self.assertIn("is_email_verified", data)
        self.assertIn("display_name", data)
        self.assertIn("date_joined", data)

    def test_me_returns_only_current_user(self):
        """Ensure /me always returns the current authenticated user"""
        other_user = User.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password="OtherPass123!"
        )

        self.authenticate(other_user)
        response = self.client.get(self.me_url)

        self.assertEqual(response.data["username"], other_user.username)
        self.assertNotEqual(response.data["username"], self.user.username)
