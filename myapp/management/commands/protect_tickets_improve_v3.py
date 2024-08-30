import time
import redis
from django.core.management.base import BaseCommand
from myapp.tasks import update_ticket_batch
from myapp.models import Ticket

BATCH_SIZE = 500
REDIS_KEY_LAST_ID = 'last_processed_id'
REDIS_KEY_ELAPSED_TIME = 'elapsed_time'

# Initialize Redis client using the Docker Redis URL
redis_client = redis.StrictRedis.from_url("redis://redis:6379/0")

class Command(BaseCommand):
    help = 'Regenerates UUIDs for all Ticket records and updates them in batches'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=BATCH_SIZE,
            help='Specify the size of batches to process at a time (default: 500)',
        )
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset the Redis checkpoint values to start from the beginning',
        )

    def handle(self, *args, **kwargs):
        batch_size = kwargs.get('batch_size', BATCH_SIZE)

        # Check if reset flag is provided
        if kwargs.get('reset'):
            self.reset_checkpoint()
            self.stdout.write(self.style.SUCCESS('Redis checkpoint values have been reset.'))

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
        """
        Returns the last processed ID and the elapsed time from Redis.
        """
        last_processed_id = redis_client.get(REDIS_KEY_LAST_ID)
        elapsed_time = redis_client.get(REDIS_KEY_ELAPSED_TIME)

        if last_processed_id is None or elapsed_time is None:
            return 0, 0.0
        return int(last_processed_id), float(elapsed_time)

    def save_checkpoint(self, last_processed_id, elapsed_time):
        """
        Saves the last processed ID and elapsed time to Redis.
        """
        redis_client.set(REDIS_KEY_LAST_ID, last_processed_id)
        redis_client.set(REDIS_KEY_ELAPSED_TIME, elapsed_time)

    def reset_checkpoint(self):
        """
        Resets the last processed ID and elapsed time in Redis.
        """
        redis_client.delete(REDIS_KEY_LAST_ID)
        redis_client.delete(REDIS_KEY_ELAPSED_TIME)
