# apps/support/services/ticket_service.py
from django.db import transaction
from apps.support.models import Ticket, TicketMessage

def assign_ticket(ticket: Ticket, staff_user, note: str = None):
    """
    Assign a ticket to staff_user and optionally add an internal note.
    """
    with transaction.atomic():
        ticket.assigned_to = staff_user
        ticket.status = Ticket.Status.IN_PROGRESS
        ticket.save(update_fields=["assigned_to", "status", "updated_at"])

        if note:
            TicketMessage.objects.create(
                ticket=ticket,
                user=staff_user,
                body=note,
                is_internal=True,
                is_from_customer=False
            )
