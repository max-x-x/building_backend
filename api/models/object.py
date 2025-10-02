import uuid
from django.db import models
from django.utils import timezone
from django.conf import settings

from api.models.timestamp import TimeStampedMixin
from api.models.user import User  # твой кастомный юзер

class ObjectStatus(models.TextChoices):
    DRAFT = "draft", "Черновик"
    ACTIVATION_PENDING = "activation_pending", "Ожидает активации"
    ACTIVE = "active", "Активен"
    SUSPENDED = "suspended", "Приостановлен"
    COMPLETED_BY_SSK = "completed_by_ssk", "Завершён ССК"
    COMPLETED = "completed", "Завершён"

class ConstructionObject(TimeStampedMixin):
    uuid_obj = models.UUIDField("ID", default=uuid.uuid4, editable=False)
    name = models.CharField("Название объекта", max_length=255)
    address = models.CharField("Адрес", max_length=500, blank=True)
    status = models.CharField(
        "Статус", max_length=32, choices=ObjectStatus.choices, default=ObjectStatus.DRAFT
    )
    ssk = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="ССК", blank=True, null=True, on_delete=models.SET_NULL, related_name="ssk_objects"
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
    
    # Ссылки на файловое хранилище
    documents_folder_url = models.URLField("URL папки с документами объекта", blank=True, help_text="Ссылка на папку с документами объекта в файловом хранилище")

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


class ObjectRoleAudit(TimeStampedMixin):
    """
    Аудит смены ответственных по объекту.
    """
    FIELD = (
        ("ssk", "ССК"),
        ("foreman", "Прораб"),
        ("iko", "ИКО"),
    )

    uuid_audit = models.UUIDField("UUID аудита", default=uuid.uuid4, editable=False)
    object = models.ForeignKey(ConstructionObject, verbose_name="Объект", on_delete=models.CASCADE, related_name="role_audit")

    field = models.CharField("Поле", max_length=16, choices=FIELD)
    old_user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="Старый пользователь", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    new_user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="Новый пользователь", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="Кем изменено", null=True, blank=True, on_delete=models.SET_NULL, related_name="object_role_changes")
    comment = models.CharField("Комментарий", max_length=500, blank=True)

    class Meta:
        verbose_name = "Аудит ролей объекта"
        verbose_name_plural = "Аудит ролей объектов"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.object_id}:{self.field} {self.old_user_id}→{self.new_user_id}"