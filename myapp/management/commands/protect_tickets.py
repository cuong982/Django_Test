import time
import uuid
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from myapp.models import Ticket

# Default batch size for processing
BATCH_SIZE = 1000


class Command(BaseCommand):
    help = 'Regenerates UUIDs for all Ticket records and updates them in batches'

    def add_arguments(self, parser):
        # Optionally allow the user to specify the batch size
        parser.add_argument(
            '--batch-size',
            type=int,
            help='Specify the size of batches to process at a time',
        )

    def handle(self, *args, **kwargs):
        # Get the batch size from command arguments or use the default
        batch_size = kwargs.get('batch_size', BATCH_SIZE)

        # Get the total number of Ticket records to display progress
        total_records = Ticket.objects.count()
        self.stdout.write(f"Total tickets: {total_records}")

        # Use a checkpoint to track the last processed record and elapsed time
        last_processed_id, previous_elapsed_time = self.get_checkpoint()

        start_time = time.time()  # Start the timer for current runtime

        while True:
            # Get the next batch of tickets starting from the last processed ID
            tickets = Ticket.objects.filter(id__gt=last_processed_id).order_by('id')[:batch_size]

            # If no tickets are left, finish the process
            if not tickets.exists():
                self.stdout.write(self.style.SUCCESS('All tickets have been processed.'))
                break

            # Process the current batch within a transaction for data integrity
            with transaction.atomic():
                for ticket in tickets:
                    ticket.token = uuid.uuid4()  # Generate a new UUID for each ticket
                    ticket.save()  # Save the updated ticket

                # Get the last processed ticket in this batch
                last_ticket = tickets[len(tickets) - 1]  # Get the last item in the sliced queryset
                last_processed_id = last_ticket.id

                # Calculate total elapsed time (including previous runs)
                elapsed_time = previous_elapsed_time + (time.time() - start_time)
                self.save_checkpoint(last_processed_id, elapsed_time)

            # Calculate and display progress and estimated time remaining
            processed_records = Ticket.objects.filter(id__lte=last_processed_id).count()
            progress = (processed_records / total_records) * 100
            estimated_total_time = (elapsed_time / processed_records) * total_records
            remaining_time = estimated_total_time - elapsed_time

            # Output progress to the console
            self.stdout.write(
                f"Processed {processed_records}/{total_records} tickets "
                f"({progress:.2f}% complete). "
                f"Estimated remaining time: {remaining_time:.2f} seconds."
            )

        # Calculate and display the total runtime after all records are processed
        total_runtime = previous_elapsed_time + (time.time() - start_time)
        self.stdout.write(self.style.SUCCESS(f"Total runtime: {total_runtime:.2f} seconds"))

    def get_checkpoint(self):
        """
        Returns the last processed ID and the elapsed time from the checkpoint file.
        """
        try:
            with open('last_processed_id.txt', 'r') as f:
                last_processed_id = int(f.readline().strip())
                elapsed_time = float(f.readline().strip())
                return last_processed_id, elapsed_time
        except (FileNotFoundError, ValueError):
            # If the file does not exist or is corrupted, start from the beginning
            return 0, 0.0

    def save_checkpoint(self, last_processed_id, elapsed_time):
        """
        Saves the last processed ID and elapsed time to the checkpoint file.
        """
        with open('last_processed_id.txt', 'w') as f:
            f.write(f"{last_processed_id}\n")
            f.write(f"{elapsed_time}\n")
