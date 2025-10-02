import uuid
from django.db import models
from django.conf import settings
from api.models.timestamp import TimeStampedMixin
from api.models.object import ConstructionObject


class DailyChecklist(TimeStampedMixin):
    STATUS = (("submitted", "Отправлен"), ("approved", "Принят"), ("rejected", "Отклонён"))

    uuid_daily = models.UUIDField("UUID чек-листа", default=uuid.uuid4, editable=False)
    object = models.ForeignKey(ConstructionObject, verbose_name="Объект", on_delete=models.CASCADE, related_name="daily_checklists")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="Автор (прораб)", on_delete=models.PROTECT, related_name="daily_reports")
    data = models.JSONField("Данные чек-листа", default=dict, blank=True)
    pdf_url = models.URLField("URL PDF")
    photos_folder_url = models.URLField("URL папки с фото", max_length=10000, blank=True)
    status = models.CharField("Статус", max_length=16, choices=STATUS, default="submitted")
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="Проверил (ССК)", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    reviewed_at = models.DateTimeField("Дата проверки", null=True, blank=True)
    review_comment = models.TextField("Комментарий проверки", blank=True)

    class Meta:
        verbose_name = "Ежедневный чек-лист"
        verbose_name_plural = "Ежедневные чек-листы"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Daily {self.object_id} [{self.status}]"
