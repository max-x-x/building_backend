import uuid
from django.db import models
from api.models.timestamp import TimeStampedMixin

class Memo(TimeStampedMixin):
    uuid_memo = models.UUIDField("UUID памятки", default=uuid.uuid4, editable=False)
    title = models.CharField("Название", max_length=300)
    pdf_url = models.URLField("URL PDF")

    class Meta:
        verbose_name = "Памятка"
        verbose_name_plural = "Памятки"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
