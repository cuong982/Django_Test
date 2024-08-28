import time
import uuid
from django.core.management.base import BaseCommand
from myapp.models import Ticket


class Command(BaseCommand):
    help = 'Create 1 million ticket records'

    def add_arguments(self, parser):
        # Adding batch_size as an optional argument
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10000,  # Default value if not passed
            help='Number of records to create per batch (default: 10000)'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']  # Get batch_size from options
        total_records = 1000000  # Total number of records to create
        records_created = 0

        start_time = time.time()  # Start time for measuring

        while records_created < total_records:
            tickets = [
                Ticket(token=uuid.uuid4(), updated=False)  # Use uuid.uuid4() to generate valid UUIDs
                for _ in range(batch_size)
            ]
            Ticket.objects.bulk_create(tickets)  # Bulk insert for performance

            records_created += batch_size

            # Calculate and display progress percentage
            progress_percentage = (records_created / total_records) * 100
            self.stdout.write(
                f'Created {records_created}/{total_records} tickets '
                f'({progress_percentage:.2f}% completed)'
            )

        end_time = time.time()  # End time for measuring
        elapsed_time = end_time - start_time

        # Convert elapsed time to minutes and seconds
        minutes, seconds = divmod(elapsed_time, 60)

        self.stdout.write(self.style.SUCCESS(
            f'Successfully created 1 million tickets in {int(minutes)} minutes and {int(seconds)} seconds'
        ))
