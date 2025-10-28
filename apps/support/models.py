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


