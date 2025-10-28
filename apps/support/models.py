# apps/support/models.py
import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.urls import reverse

User = settings.AUTH_USER_MODEL  # will use get_user_model() in code that imports

class Ticket(models.Model):
    """
    Support ticket / case for customer issues.
    - Use UUID as PK for safer public references.
    - Tickets can be linked to an Order (optional).
    - Tickets are created by users (or staff on behalf).
    """
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        PENDING = "PENDING", "Pending"           # waiting customer or external
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        RESOLVED = "RESOLVED", "Resolved"
        CLOSED = "CLOSED", "Closed"
        ESCALATED = "ESCALATED", "Escalated"

    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        URGENT = "URGENT", "Urgent"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference = models.CharField(max_length=36, unique=True, blank=True)  # human friendly ref (e.g. SUP-2025-0001)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # relations
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tickets_created")
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="tickets_assigned")
    # optional tie to order (imports lazy to avoid circular)
    order = models.ForeignKey("orders.Order", null=True, blank=True, on_delete=models.SET_NULL, related_name="support_tickets")

    # properties
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    is_public = models.BooleanField(default=True, help_text="If false, ticket is internal to staff.")
    tags = models.JSONField(default=list, blank=True, help_text="List of string tags for filtering/analytics")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity_at = models.DateTimeField(null=True, blank=True)

    # SLA fields (optional, for enterprise use)
    sla_due_at = models.DateTimeField(null=True, blank=True, help_text="Time by which ticket should be responded/resolved")

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["creator", "status"]),
            models.Index(fields=["assigned_to", "status"]),
            models.Index(fields=["priority", "status"]),
        ]
        verbose_name = "Support Ticket"
        verbose_name_plural = "Support Tickets"

    def __str__(self):
        return f"{self.reference or str(self.id)} — {self.title}"


