from django.db import models
from django.contrib.auth.models import AbstractUser
from phonenumber_field.modelfields import PhoneNumberField
from apps.users.utils.default_country import get_default_country
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

# A dedicated model for countries
class Country(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=2, unique=True)  # e.g., 'NP'

    def __str__(self):
        return self.name

# A dedicated model for states/regions within a country
class State(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='states')
    name = models.CharField(max_length=120)

    class Meta:
        # Prevents a state with the same name existing twice for one country
        unique_together = ('country', 'name')

    def __str__(self):
        return self.name


class Address(models.Model):
    ADDRESS_TYPE_CHOICES = [
        ("billing", "Billing"),
        ("shipping", "Shipping"),
        ("work", "Work"),
        ("home", "Home"),
        ("other", "Other"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    address_type = models.CharField(max_length=20, choices=ADDRESS_TYPE_CHOICES, default="home")

    recipient_name = models.CharField(max_length=255)
    # phone_number = models.CharField(max_length=20, blank=True, null=True)
    phone_number = PhoneNumberField(blank=True, null=True) # Using PhoneNumberField for better phone number handling
    street_address = models.CharField(max_length=255)
    city = models.CharField(max_length=120)
    postal_code = models.CharField(max_length=20)
    country = models.ForeignKey(Country, on_delete=models.PROTECT, default=get_default_country) # Critical lookup tables, non-negotiable relationships.
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True, blank=True) # Optional relationships, preserving data after a link is broken.

    is_default = models.BooleanField(default=False, help_text="Designates this address as the user's primary. There can only be one primary address per user, and this must be managed by the application logic.")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Addresses"
        ordering = ['-is_default', '-created_at']
        indexes = [
        models.Index(fields=["user", "is_default"]),
        models.Index(fields=["postal_code"]),   
            ]
        constraints = [
            models.UniqueConstraint(
                    fields=["user", "address_type", "street_address", "city", "state", "postal_code", "country"],
                    name="unique_user_address"
            )
        ]
    
    def save(self, *args, **kwargs):
        """ Ensure only one default address per user as this method guarantees that every time an address is marked as default, any previous default address for that user is automatically unset."""
        if not self.recipient_name:
            self.recipient_name = f"{self.user.first_name} {self.user.last_name}".strip() or self.user.username
        if self.is_default:
            # Unset the old default address for this user
            Address.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)
   
        
    def __str__(self):
        return f"{self.recipient_name} - {self.street_address}, {self.city}"

class UserActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    # added
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    extra_data = models.JSONField(default= dict, blank=True)
    outcome = models.CharField(max_length=20, default="SUCCESS", choices=[
        ("SUCCESS", "Success"),
        ("FAILURE", "Failure"),
        ("BLOCKED", "Blocked")
    ])

    class Meta:
        indexes = [
            models.Index(fields=['user', 'timestamp']),
        ]
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.username} - {self.action} at {self.timestamp}"

class PasswordHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_history')
    password_hash = models.CharField(max_length=128)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - Password Changed at {self.timestamp}"


