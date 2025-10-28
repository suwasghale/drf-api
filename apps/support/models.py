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

    def save(self, *args, **kwargs):
        # generate a readable reference once on create
        if not self.reference:
            # e.g. SUP-2025-00001 (simple approach)
            prefix = "SUP"
            date_part = timezone.now().strftime("%Y%m%d")
            # fallback: use part of uuid to avoid race; for sequential you'd use a counter table
            self.reference = f"{prefix}-{date_part}-{str(self.id)[:8].upper()}"
        if not self.last_activity_at:
            self.last_activity_at = timezone.now()
        super().save(*args, **kwargs)

    @property
    def is_open(self):
        return self.status in {self.Status.OPEN, self.Status.PENDING, self.Status.IN_PROGRESS, self.Status.ESCALATED}

    def mark_activity(self):
        """Touch last_activity_at to now."""
        self.last_activity_at = timezone.now()
        self.save(update_fields=["last_activity_at"])

class TicketMessage(models.Model):
    """
    Messages / replies inside a ticket thread.
    Each message can optionally have attachments and can be marked internal (staff-only).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="messages")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="support_messages")
    body = models.TextField()
    is_internal = models.BooleanField(default=False, help_text="Internal staff note - not visible to customer")
    created_at = models.DateTimeField(auto_now_add=True)
    # quick flags
    is_from_customer = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["ticket", "created_at"]),
            models.Index(fields=["user", "created_at"]),
        ]

    def __str__(self):
        return f"Message by {self.user} on {self.ticket.reference}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update ticket last_activity_at
        Ticket.objects.filter(pk=self.ticket_id).update(last_activity_at=self.created_at)



class MessageAttachment(models.Model):
    """
    Stores attachment files for ticket messages.
    Keep attachments small and validate file types in serializer or storage layer.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(TicketMessage, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="support/attachments/%Y/%m/%d/")
    file_name = models.CharField(max_length=255, blank=True)
    content_type = models.CharField(max_length=255, blank=True)
    size = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["message", "created_at"])]
        verbose_name = "Message Attachment"
        verbose_name_plural = "Message Attachments"

    def save(self, *args, **kwargs):
        if not self.file_name and self.file:
            self.file_name = self.file.name
        if self.file and not self.size:
            try:
                self.size = self.file.size
            except Exception:
                self.size = None
        super().save(*args, **kwargs)

