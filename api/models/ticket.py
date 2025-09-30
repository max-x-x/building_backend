import uuid
from django.db import models
from django.conf import settings
from api.models.timestamp import TimeStampedMixin
from api.models.object import ConstructionObject

# TODO убрать
class Ticket(TimeStampedMixin):
    STATUS = (("open", "Открыт"), ("in_progress", "В работе"), ("done", "Закрыт"))

    uuid_ticket = models.UUIDField("UUID тикета", default=uuid.uuid4, editable=False)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="Автор", on_delete=models.PROTECT, related_name="tickets")
    object = models.ForeignKey(ConstructionObject, verbose_name="Объект", null=True, blank=True, on_delete=models.SET_NULL, related_name="tickets")
    text = models.TextField("Текст обращения")
    status = models.CharField("Статус", max_length=16, choices=STATUS, default="open")

    class Meta:
        verbose_name = "Тикет"
        verbose_name_plural = "Тикеты"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Ticket {self.author_id} [{self.get_status_display()}]"
