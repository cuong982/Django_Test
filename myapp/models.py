from django.db import models
import uuid


class Ticket(models.Model):
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    updated = models.BooleanField(default=False)

    def __str__(self):
        return str(self.token)
