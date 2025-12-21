from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class LoginSecurityAPITestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="secureuser",
            email="secure@example.com",
            password="CorrectPass123!"
        )
        self.url = reverse("auth-login")

    def test_failed_login_increments_attempts(self):
        for _ in range(3):
            self.client.post(self.url, {
                "identifier": "secureuser",
                "password": "WrongPass"
            })

        self.user.refresh_from_db()
        self.assertGreater(self.user.failed_login_attempts, 0)

    def test_account_locks_after_max_attempts(self):
        for _ in range(5):
            self.client.post(self.url, {
                "identifier": "secureuser",
                "password": "WrongPass"
            })

        self.user.refresh_from_db()
        self.assertTrue(self.user.is_locked)

    def test_locked_account_cannot_login(self):
        self.user.is_locked = True
        self.user.save()

        response = self.client.post(self.url, {
            "identifier": "secureuser",
            "password": "CorrectPass123!"
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
