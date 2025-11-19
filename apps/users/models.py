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
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=50, choices=Roles.choices, default=Roles.USER)    
    display_name = models.CharField(max_length=255, blank=True, null=True)
    profile_image = models.ImageField(upload_to="users/", blank=True, null=True)

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


class UserActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    # 🧠 Additional metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    extra_data = models.JSONField(default=dict, blank=True)

    outcome = models.CharField(
        max_length=20,
        default="SUCCESS",
        choices=[
            ("SUCCESS", "Success"),
            ("FAILURE", "Failure"),
            ("BLOCKED", "Blocked"),
        ]
    )

    class Meta:
        indexes = [
            models.Index(fields=['user', 'timestamp']),
        ]
        ordering = ['-timestamp']
        verbose_name = "User Activity Log"
        verbose_name_plural = "User Activity Logs"

    def __str__(self):
        return f"{self.user.username} - {self.action} at {self.timestamp}"
