from celery import shared_task
from myapp.models import Ticket
import uuid


@shared_task
def update_ticket_batch(start_id, end_id):
    tickets = Ticket.objects.filter(id__gte=start_id, id__lte=end_id)
    for ticket in tickets:
        ticket.token = uuid.uuid4()
    Ticket.objects.bulk_update(tickets, ['token'])
