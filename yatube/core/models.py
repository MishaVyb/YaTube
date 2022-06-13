from django.db import models


class CreatedModel(models.Model):
    """Abstract model with auto filled created date and ordering by it."""

    created = models.DateTimeField(
        'Дата создания', auto_now_add=True, db_index=True
    )

    class Meta:
        abstract = True
        ordering = ['-created']
