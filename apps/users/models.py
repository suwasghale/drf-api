from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.
class User(AbstractUser):
    """
    Custom User Model extending Django's AbstractUser. 
    We can add extra fields as needed.
    """
    class Roles(models.TextChoices):
        USER = "USER", "User"
        VENDOR = "VENDOR", "Vendor"
        STAFF = "STAFF", "Staff"
        SUPERADMIN = "SUPERADMIN", "Superadmin"

    role = models.CharField(max_length=50, choices=Roles.choices, default=Roles.USER)    
    display_name = models.CharField(max_length=255, blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    last_failed_login_attempt = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.username
class PasswordHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_history')
    password_hash = models.CharField(max_length=128)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - Password Changed at {self.timestamp}"


