from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class ChangePasswordAPITestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="OldPass123!"
        )
        self.url = reverse("profile-change-password")

    def authenticate(self):
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}"
        )

    def test_authentication_required(self):
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_wrong_old_password_fails(self):
        self.authenticate()
        response = self.client.post(self.url, {
            "old_password": "WrongPass",
            "new_password": "NewStrongPass123!"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_change_success(self):
        self.authenticate()
        response = self.client.post(self.url, {
            "old_password": "OldPass123!",
            "new_password": "NewStrongPass123!"
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewStrongPass123!"))
