import uuid
from django.db import models
from django.conf import settings
from api.models.timestamp import TimeStampedMixin
from api.models.object import ConstructionObject

class Folder(TimeStampedMixin):
    uuid_folder = models.UUIDField("UUID папки", default=uuid.uuid4, editable=False)
    object = models.ForeignKey(
        ConstructionObject, verbose_name="Объект",
        on_delete=models.CASCADE, related_name="folders"
    )
    name = models.CharField("Название папки", max_length=255)
    parent = models.ForeignKey(
        "self", verbose_name="Родительская папка",
        null=True, blank=True, on_delete=models.CASCADE, related_name="children"
    )

    class Meta:
        verbose_name = "Папка"
        verbose_name_plural = "Папки"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} (obj={self.object_id})"

# TODO убрать
class DocumentFile(TimeStampedMixin):
    uuid_document = models.UUIDField("UUID файла", default=uuid.uuid4, editable=False)
    object = models.ForeignKey(
        ConstructionObject, verbose_name="Объект",
        on_delete=models.CASCADE, related_name="documents"
    )
    folder = models.ForeignKey(
        Folder, verbose_name="Папка",
        null=True, blank=True, on_delete=models.SET_NULL, related_name="files"
    )
    name = models.CharField("Название файла", max_length=255)
    url = models.URLField("URL файла")
    size_bytes = models.BigIntegerField("Размер, байт", null=True, blank=True)
    content_type = models.CharField("MIME-тип", max_length=128, blank=True)

    class Meta:
        verbose_name = "Файл"
        verbose_name_plural = "Файлы"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.content_type or 'unknown'})"

class ExecDocument(TimeStampedMixin):
    KIND = (
        ("general", "Общее"),
        ("activation", "Активация"),
        ("completion", "Завершение"),
        ("other", "Другое"),
    )
    uuid_execdoc = models.UUIDField("UUID сборника ИД", default=uuid.uuid4, editable=False)
    object = models.ForeignKey(
        ConstructionObject, verbose_name="Объект",
        on_delete=models.CASCADE, related_name="exec_docs"
    )
    kind = models.CharField("Тип сборника", max_length=32, choices=KIND, default="general")
    pdf_url = models.URLField("URL PDF сборника")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Создал",
        null=True, blank=True, on_delete=models.SET_NULL
    )

    class Meta:
        verbose_name = "Сборник исполнительной документации"
        verbose_name_plural = "Сборники ИД"
        ordering = ["-created_at"]

    def __str__(self):
        return f"ИД {self.object_id} [{self.get_kind_display()}]"
