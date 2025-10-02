import uuid
from django.db import models
from django.conf import settings

from api.models.timestamp import TimeStampedMixin
from api.models.object import ConstructionObject


class Prescription(TimeStampedMixin):
    STATUS = (
        ("open", "Открыто"),
        ("awaiting_verification", "Ожидает проверки"),
        ("closed", "Закрыто"),
    )

    uuid_prescription = models.UUIDField("UUID предписания", default=uuid.uuid4, editable=False)
    object = models.ForeignKey(ConstructionObject, verbose_name="Объект", on_delete=models.CASCADE, related_name="prescriptions")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="Автор (ИКО/ССК)", on_delete=models.PROTECT, related_name="prescriptions_created")
    title = models.CharField("Заголовок", max_length=255)
    description = models.TextField("Описание", blank=True)
    requires_stop = models.BooleanField("Требует приостановки работ", default=False)
    requires_personal_recheck = models.BooleanField("Нужна личная перепроверка", default=False)
    attachments = models.JSONField("Вложения (URL'ы)", default=list, blank=True)
    status = models.CharField("Статус", max_length=32, choices=STATUS, default="open")
    closed_at = models.DateTimeField("Закрыто", null=True, blank=True)
    
    violation_photos_folder_url = models.JSONField("URL папки с фото нарушения", default=list, blank=True, help_text="Массив ссылок на фото нарушения в файловом хранилище")

    class Meta:
        verbose_name = "Предписание"
        verbose_name_plural = "Предписания"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Prescription[{self.pk}] {self.object.name} — {self.get_status_display()}"


class PrescriptionFix(TimeStampedMixin):
    uuid_fix = models.UUIDField("UUID исправления", default=uuid.uuid4, editable=False)
    prescription = models.ForeignKey(Prescription, verbose_name="Предписание", on_delete=models.CASCADE, related_name="fixes")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="Кто исправил (Прораб)", on_delete=models.PROTECT)
    comment = models.TextField("Комментарий")
    attachments = models.JSONField("Вложения (URL'ы)", default=list, blank=True)
    
    fix_photos_folder_url = models.JSONField("URL папки с фото исправления", default=list, blank=True, help_text="Массив ссылок на фото исправления нарушения в файловом хранилище")

    class Meta:
        verbose_name = "Исправление предписания"
        verbose_name_plural = "Исправления предписаний"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Fix[{self.pk}] for Prescription[{self.prescription_id}]"
