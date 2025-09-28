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


class ObjectActivation(TimeStampedMixin):
    """
    Заявка на активацию объекта:
    - создаёт ССК
    - согласует ИКО (выезд, чек-лист)
    """
    STATUS = (
        ("requested", "Заявка отправлена (ССК)"),
        ("visit_planned", "Визит ИКО запланирован"),
        ("checked", "ИКО провёл проверку"),
        ("approved", "Активация одобрена ИКО"),
        ("rejected", "Отклонена ИКО"),
    )

    uuid_activation = models.UUIDField("UUID активации", default=uuid.uuid4, editable=False)
    object = models.ForeignKey(ConstructionObject, verbose_name="Объект", on_delete=models.CASCADE, related_name="activations")
    status = models.CharField("Статус", max_length=32, choices=STATUS, default="requested")

    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="ССК-инициатор", on_delete=models.PROTECT, related_name="activation_requests")
    ssk_checklist = models.JSONField("Чек-лист ССК", default=dict, blank=True)
    ssk_checklist_pdf = models.URLField("PDF чек-лист ССК", blank=True)
    requested_at = models.DateTimeField("Отправлено", default=timezone.now)

    iko_checklist = models.JSONField("Чек-лист ИКО", default=dict, blank=True)
    iko_checklist_pdf = models.URLField("PDF чек-лист ИКО", blank=True)
    iko_has_violations = models.BooleanField("Найдены нарушения ИКО", default=False)
    iko_checked_at = models.DateTimeField("Проверено ИКО", null=True, blank=True)
    approved_at = models.DateTimeField("Одобрено ИКО", null=True, blank=True)
    rejected_reason = models.TextField("Причина отклонения", blank=True)

    class Meta:
        verbose_name = "Активация объекта"
        verbose_name_plural = "Активации объектов"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Activation[{self.pk}] {self.object.name} — {self.get_status_display()}"