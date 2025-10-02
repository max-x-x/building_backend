import uuid
from django.db import models
from django.conf import settings
from api.models.timestamp import TimeStampedMixin
from api.models.object import ConstructionObject

class Delivery(TimeStampedMixin):
    STATUS = (
        ("scheduled", "Запланирована"),
        ("received", "Получена"),
        ("accepted", "Принята ССК"),
        ("rejected", "Отклонена ССК"),
        ("sent_to_lab", "Отправлена в лабораторию"),
        ("awaiting_lab", "Ожидание результатов"),
    )

    uuid_delivery = models.UUIDField("UUID поставки", default=uuid.uuid4, editable=False)
    object = models.ForeignKey(ConstructionObject, verbose_name="Объект", on_delete=models.CASCADE, related_name="deliveries")
    planned_date = models.DateField("Плановая дата", null=True, blank=True)
    notes = models.TextField("Примечания", blank=True)
    status = models.CharField("Статус", max_length=20, choices=STATUS, default="scheduled")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="Инициатор (ССК)", on_delete=models.PROTECT, related_name="deliveries_created")
    
    # Ссылки на файловое хранилище
    invoice_photos_folder_url = models.JSONField("URL папки с фото накладных", default=list, blank=True, help_text="Массив ссылок на фото накладных в файловом хранилище")

    class Meta:
        verbose_name = "Поставка"
        verbose_name_plural = "Поставки"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Delivery {self.object_id} [{self.get_status_display()}]"


class Invoice(TimeStampedMixin):
    uuid_invoice = models.UUIDField("UUID накладной", default=uuid.uuid4, editable=False)
    object = models.ForeignKey(ConstructionObject, verbose_name="Объект", on_delete=models.CASCADE, related_name="invoices")
    delivery = models.ForeignKey(Delivery, verbose_name="Поставка", on_delete=models.CASCADE, related_name="invoices")
    pdf_url = models.URLField("URL PDF/фото накладной")
    folder_url = models.URLField("URL папки на FTP", max_length=10000, blank=True, help_text="Ссылка на папку с файлами на FTP сервере")
    data = models.JSONField("Распознанные данные", default=dict, blank=True)

    class Meta:
        verbose_name = "Накладная/ТТН"
        verbose_name_plural = "Накладные/ТТН"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Invoice {self.object_id} for delivery {self.delivery_id}"


class Material(TimeStampedMixin):
    """Материал из распознанной накладной."""
    uuid_material = models.UUIDField("UUID материала", default=uuid.uuid4, editable=False)
    delivery = models.ForeignKey(Delivery, verbose_name="Поставка", on_delete=models.CASCADE, related_name="materials")
    invoice = models.ForeignKey(Invoice, verbose_name="Накладная", on_delete=models.CASCADE, related_name="materials")
    
    # Поля из распознанных данных
    material_name = models.CharField("Наименование материала", max_length=255)
    material_quantity = models.CharField("Количество материала", max_length=100, blank=True)
    material_size = models.CharField("Размер", max_length=100, blank=True)
    material_volume = models.CharField("Объем", max_length=100, blank=True)
    material_netto = models.CharField("Нетто", max_length=100, blank=True)
    
    # Статус материала (для отслеживания изменений)
    is_confirmed = models.BooleanField("Подтвержден", default=False)

    class Meta:
        verbose_name = "Материал"
        verbose_name_plural = "Материалы"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.material_name} - {self.material_quantity}"


class LabOrder(TimeStampedMixin):
    STATUS = (("sent", "Отправлено"), ("done", "Готово"))

    uuid_lab_order = models.UUIDField("UUID заказа в лабораторию", default=uuid.uuid4, editable=False)
    delivery = models.ForeignKey(Delivery, verbose_name="Поставка", on_delete=models.CASCADE, related_name="lab_orders")
    items = models.JSONField("Отобранные образцы", default=list, blank=True)  # [{invoice_item_id, sample_code}]
    status = models.CharField("Статус", max_length=16, choices=STATUS, default="sent")

    class Meta:
        verbose_name = "Лабораторное исследование"
        verbose_name_plural = "Лабораторные исследования"
        ordering = ["-created_at"]

    def __str__(self):
        return f"LabOrder for delivery {self.delivery_id} [{self.status}]"
