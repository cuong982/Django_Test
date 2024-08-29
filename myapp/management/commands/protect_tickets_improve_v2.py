import time
from django.core.management.base import BaseCommand
from myapp.tasks import update_ticket_batch
from myapp.models import Ticket

BATCH_SIZE = 500
CHECKPOINT_FILE = 'last_processed_id.txt'


class Command(BaseCommand):
    help = 'Regenerates UUIDs for all Ticket records and updates them in batches'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=BATCH_SIZE,
            help='Specify the size of batches to process at a time (default: 500)',
        )

    def handle(self, *args, **kwargs):
        batch_size = kwargs.get('batch_size', BATCH_SIZE)
        total_records = Ticket.objects.count()

        if total_records == 0:
            self.stdout.write(self.style.WARNING('No tickets found to process.'))
            return

        self.stdout.write(f"Total tickets: {total_records}")

        last_processed_id, previous_elapsed_time = self.get_checkpoint()

        start_time = time.time()

        while True:
            tickets = Ticket.objects.filter(id__gt=last_processed_id).order_by('id')[:batch_size]

            if not tickets.exists():
                self.stdout.write(self.style.SUCCESS('All tickets have been processed.'))
                break

            # Get the IDs of the first and last tickets in this batch
            start_id = tickets[0].id
            end_id = tickets[len(tickets) - 1].id

            # Dispatch the task to Celery
            update_ticket_batch.delay(start_id, end_id)

            last_processed_id = end_id
            elapsed_time = previous_elapsed_time + (time.time() - start_time)
            self.save_checkpoint(last_processed_id, elapsed_time)

            processed_records = Ticket.objects.filter(id__lte=last_processed_id).count()
            progress = (processed_records / total_records) * 100
            estimated_total_time = (elapsed_time / processed_records) * total_records
            remaining_time = estimated_total_time - elapsed_time

            self.stdout.write(
                f"Processed {processed_records}/{total_records} tickets "
                f"({progress:.2f}% complete). "
                f"Estimated remaining time: {remaining_time:.2f} seconds."
            )

        total_runtime = previous_elapsed_time + (time.time() - start_time)
        self.stdout.write(self.style.SUCCESS(f"Total runtime: {total_runtime:.2f} seconds"))

    def get_checkpoint(self):
        try:
            with open(CHECKPOINT_FILE, 'r') as f:
                last_processed_id = int(f.readline().strip())
                elapsed_time = float(f.readline().strip())
                return last_processed_id, elapsed_time
        except (FileNotFoundError, ValueError):
            return 0, 0.0

    def save_checkpoint(self, last_processed_id, elapsed_time):
        with open(CHECKPOINT_FILE, 'w') as f:
            f.write(f"{last_processed_id}\n")
            f.write(f"{elapsed_time}\n")
