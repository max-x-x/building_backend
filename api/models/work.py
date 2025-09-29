import uuid
from django.db import models
from django.conf import settings
from api.models.timestamp import TimeStampedMixin
from api.models.object import ConstructionObject

class Work(TimeStampedMixin):
    STATUS = (("open", "Открыта"), ("in_progress", "В работе"), ("done", "Выполнена"))

    uuid_work = models.UUIDField("UUID работы", default=uuid.uuid4, editable=False)
    object = models.ForeignKey(ConstructionObject, verbose_name="Объект", on_delete=models.CASCADE, related_name="works")
    title = models.CharField("Название работы/задачи", max_length=300)
    status = models.CharField("Статус", max_length=16, choices=STATUS, default="open")
    responsible = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="Ответственный", on_delete=models.PROTECT, related_name="works_responsible")
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="Проверяющий", on_delete=models.PROTECT, related_name="works_reviewer")

    class Meta:
        verbose_name = "Работа/задача по объекту"
        verbose_name_plural = "Работы/задачи по объектам"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
