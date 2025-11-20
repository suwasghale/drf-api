from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.hashers import make_password
from django.utils import timezone

class User(AbstractUser):

    class Roles(models.TextChoices):
        USER = "USER", "User"
        VENDOR = "VENDOR", "Vendor"
        STAFF = "STAFF", "Staff"
        SUPERADMIN = "SUPERADMIN", "Superadmin"

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=50, choices=Roles.choices, default=Roles.USER)
    display_name = models.CharField(max_length=255, blank=True, null=True)
    profile_image = models.ImageField(upload_to="users/", blank=True, null=True)

    # Verification & security
    is_email_verified = models.BooleanField(default=False)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    last_failed_login_attempt = models.DateTimeField(null=True, blank=True)
    is_locked = models.BooleanField(default=False)
    lock_expires_at = models.DateTimeField(null=True, blank=True)

    # Soft delete
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return f"{self.email} ({self.username})"

class PasswordHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_history')
    password_hash = models.CharField(max_length=128)
    timestamp = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.password_hash.startswith("pbkdf2"):
            self.password_hash = make_password(self.password_hash)

        super().save(*args, **kwargs)

        # Keep last 5 passwords only
        history = PasswordHistory.objects.filter(user=self.user).order_by('-timestamp')
        if history.count() > 5:
            to_delete = history[5:]
            PasswordHistory.objects.filter(id__in=[p.id for p in to_delete]).delete()

    def __str__(self):
        return f"{self.user.email} - Password changed on {self.timestamp}"
class UserActivityLog(models.Model):

    class ActionTypes(models.TextChoices):
        LOGIN = "LOGIN", "Login"
        LOGOUT = "LOGOUT", "Logout"
        FAILED_LOGIN = "FAILED_LOGIN", "Failed Login"
        PASSWORD_RESET = "PASSWORD_RESET", "Password Reset"
        EMAIL_VERIFICATION = "EMAIL_VERIFICATION", "Email Verification"
        UPDATE_PROFILE = "UPDATE_PROFILE", "Updated Profile"
        PASSWORD_CHANGE = "PASSWORD_CHANGE", "Password Change"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    action_type = models.CharField(max_length=50, choices=ActionTypes.choices)
    timestamp = models.DateTimeField(auto_now_add=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True, unpack_ipv4=True)
    user_agent = models.TextField(null=True, blank=True)
    device = models.CharField(max_length=255, null=True, blank=True)
    os = models.CharField(max_length=255, null=True, blank=True)
    browser = models.CharField(max_length=255, null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    session_id = models.CharField(max_length=255, null=True, blank=True)
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
        ordering = ['-timestamp']
        indexes = [models.Index(fields=['user', 'timestamp'])]

    def __str__(self):
        return f"{self.user.email} - {self.action_type}"
