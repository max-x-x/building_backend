import uuid
from django.db import models
from django.conf import settings

from api.models.object import ConstructionObject
from api.models.timestamp import TimeStampedMixin


class WorkPlan(TimeStampedMixin):
    uuid_wp = models.UUIDField("ID", default=uuid.uuid4, editable=False)
    object = models.ForeignKey(ConstructionObject, verbose_name="Объект", on_delete=models.CASCADE, related_name="work_plans")
    title = models.CharField("Название перечня", max_length=255, blank=True, help_text="Для удобства поиска/версий")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="Создал (ССК/админ)", on_delete=models.PROTECT, related_name="created_work_plans")

    class Meta:
        verbose_name = "Перечень работ"
        verbose_name_plural = "Перечни работ"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title or 'Перечень'} для {self.object.name}"


class WorkItem(TimeStampedMixin):
    uuid_wi = models.UUIDField("ID", default=uuid.uuid4, editable=False)
    plan = models.ForeignKey(WorkPlan, verbose_name="Перечень", on_delete=models.CASCADE, related_name="items")
    name = models.CharField("Наименование работы", max_length=300)
    quantity = models.DecimalField("Количество", max_digits=12, decimal_places=2, null=True, blank=True)
    unit = models.CharField("Ед. изм.", max_length=32, blank=True)
    start_date = models.DateField("Дата начала")
    end_date = models.DateField("Дата окончания")
    document_url = models.URLField("Ссылка на документ", blank=True)

    class Meta:
        verbose_name = "Позиция перечня работ"
        verbose_name_plural = "Позиции перечня работ"
        ordering = ["start_date", "name"]

    def __str__(self):
        return f"{self.name} ({self.start_date} → {self.end_date})"


class ScheduleItem(TimeStampedMixin):
    STATUS_CHOICES = (
        ("planned", "Запланировано"),
        ("in_progress", "В работе"),
        ("done", "Выполнено"),
    )

    uuid_schedule = models.UUIDField("ID", default=uuid.uuid4, editable=False)
    object = models.ForeignKey(ConstructionObject, verbose_name="Объект", on_delete=models.CASCADE, related_name="schedule_items")
    work_item = models.OneToOneField(WorkItem, verbose_name="Позиция перечня", on_delete=models.CASCADE, related_name="schedule_item")
    planned_start = models.DateField("План. начало")
    planned_end = models.DateField("План. окончание")
    status = models.CharField("Статус", max_length=16, choices=STATUS_CHOICES, default="planned")

    class Meta:
        verbose_name = "Элемент расписания"
        verbose_name_plural = "Расписание объекта"
        ordering = ["planned_start", "planned_end"]

    def __str__(self):
        return f"{self.work_item.name} [{self.planned_start} — {self.planned_end}]"
