import uuid
from django.db import models
from django.conf import settings

from api.models.timestamp import TimeStampedMixin
from api.models.object import ConstructionObject

class VisitRequest(TimeStampedMixin):
    STATUS = (
        ("pending", "Ожидает QR"),
        ("qr_assigned", "QR назначен"),
        ("done", "Визит состоялся"),
        ("cancelled", "Отменено"),
    )

    uuid_visit = models.UUIDField("UUID заявки", default=uuid.uuid4, editable=False)
    object = models.ForeignKey(ConstructionObject, verbose_name="Объект", on_delete=models.CASCADE, related_name="visit_requests")
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="Кто запросил", on_delete=models.PROTECT, related_name="visit_requests_created")
    planned_at = models.DateTimeField("Планируемое время", null=True, blank=True)
    status = models.CharField("Статус", max_length=16, choices=STATUS, default="pending")

    class Meta:
        verbose_name = "Заявка на посещение"
        verbose_name_plural = "Заявки на посещение"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Visit[{self.pk}] {self.object.name} — {self.get_status_display()}"

class QrCode(TimeStampedMixin):
    uuid_qr = models.UUIDField("UUID QR", default=uuid.uuid4, editable=False)
    object = models.ForeignKey(ConstructionObject, verbose_name="Объект", on_delete=models.CASCADE, related_name="qr_codes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="Кому выдан (обычно ИКО)", on_delete=models.PROTECT, related_name="qr_codes")
    token = models.UUIDField("Токен QR", default=uuid.uuid4, editable=False, db_index=True)
    valid_from = models.DateTimeField("Действителен с")
    valid_to = models.DateTimeField("Действителен до")
    geojson = models.JSONField("Геофенс (полигон/мультиполигон)", default=dict, blank=True)

    class Meta:
        verbose_name = "QR-код посещения"
        verbose_name_plural = "QR-коды посещений"
        ordering = ["-created_at"]

    def __str__(self):
        return f"QR[{self.pk}] {self.user.email} @ {self.object.name}"
