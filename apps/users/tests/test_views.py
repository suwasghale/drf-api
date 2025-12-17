from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class UserMeAPITestCase(APITestCase):
    
    def setUp(self):
        # create test user
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpassword', 
            email='test@testuser.com')
        # actual url
        self.me_url = reverse('profile-me')

    def test_me_requires_authentication(self):
        """Ensure /me cannot be accessed without authentication"""
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_me_returns_correct_user_data(self):
        """Authenticated user should get correct data"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        self.assertEqual(data["username"], self.user.username)
        self.assertEqual(data["email"], self.user.email)
        self.assertNotIn("password", data)
        self.assertIn("is_email_verified", data)
        self.assertIn("display_name", data)
        self.assertIn("date_joined", data)
    


    def test_me_only_returns_authenticated_user(self):
        """Ensure /me always returns current user"""
        other_user = User.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password="OtherPass123!"
        )
        self.client.force_authenticate(user=other_user)
        response = self.client.get(self.me_url)
        self.assertEqual(response.data["username"], other_user.username)
        self.assertNotEqual(response.data["username"], self.user.username)