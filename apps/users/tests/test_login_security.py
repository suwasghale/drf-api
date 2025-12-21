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

