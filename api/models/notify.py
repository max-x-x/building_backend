import uuid
from django.db import models
from django.conf import settings

from api.models.timestamp import TimeStampedMixin
from api.models.object import ConstructionObject

# TODO убрать
class Notification(TimeStampedMixin):
    """
    Уведомление (для пользователей/ролей по объекту).
    """
    TYPE = (
        ("activation_requested", "Запрошена активация"),
        ("iko_assigned", "Назначен ИКО"),
        ("status_changed", "Смена статуса объекта"),
        ("suspended", "Объект приостановлен"),
        ("resumed", "Объект возобновлён"),
        ("completed", "Объект завершён"),
    )

    uuid_notification = models.UUIDField("UUID уведомления", default=uuid.uuid4, editable=False)
    object = models.ForeignKey(ConstructionObject, verbose_name="Объект", on_delete=models.CASCADE, related_name="notifications")
    to_user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="Кому", on_delete=models.CASCADE, related_name="notifications", null=True, blank=True)
    to_role = models.CharField("Роль (если широкая рассылка)", max_length=16, blank=True)
    type = models.CharField("Тип", max_length=32, choices=TYPE)
    payload = models.JSONField("Данные", default=dict, blank=True)
    is_read = models.BooleanField("Прочитано", default=False)

    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"
        ordering = ["-created_at"]

    def __str__(self):
        target = self.to_user.email if self.to_user else self.to_role or "all"
        return f"Notify[{self.pk}] {self.type} -> {target}"
