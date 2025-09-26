import uuid
from django.db import models
from django.utils import timezone
from django.conf import settings

from api.models.timestamp import TimeStampedMixin
from api.models.user import User  # твой кастомный юзер

class ConstructionObject(TimeStampedMixin):
    uuid_obj = models.UUIDField("ID", default=uuid.uuid4, editable=False)
    name = models.CharField("Название объекта", max_length=255)
    address = models.CharField("Адрес", max_length=500, blank=True)
    ssk = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="ССК",
        on_delete=models.PROTECT, related_name="ssk_objects"
    )
    foreman = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Прораб",
        null=True, blank=True, on_delete=models.SET_NULL, related_name="foreman_objects"
    )
    iko = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="ИКО",
        null=True, blank=True, on_delete=models.SET_NULL, related_name="iko_objects"
    )
    can_proceed = models.BooleanField("Можно продолжать стройку", default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Кем создан",
        null=True, blank=True, on_delete=models.SET_NULL, related_name="created_objects"
    )

    class Meta:
        verbose_name = "Объект строительства"
        verbose_name_plural = "Объекты строительства"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.address})"
