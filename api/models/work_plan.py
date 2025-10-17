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
        ("completed_foreman", "Завершено прорабом"),
        ("completed_ssk", "Завершено ССК"),
    )

    uuid_schedule = models.UUIDField("ID", default=uuid.uuid4, editable=False)
    object = models.ForeignKey(ConstructionObject, verbose_name="Объект", on_delete=models.CASCADE, related_name="schedule_items")
    work_item = models.OneToOneField(WorkItem, verbose_name="Позиция перечня", on_delete=models.CASCADE, related_name="schedule_item")
    planned_start = models.DateField("План. начало")
    planned_end = models.DateField("План. окончание")
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default="planned")

    class Meta:
        verbose_name = "Элемент расписания"
        verbose_name_plural = "Расписание объекта"
        ordering = ["planned_start", "planned_end"]

    def __str__(self):
        return f"{self.work_item.name} [{self.planned_start} — {self.planned_end}]"


class WorkPlanVersion(TimeStampedMixin):
    uuid_wp_version = models.UUIDField("UUID версии перечня", default=uuid.uuid4, editable=False)
    plan = models.ForeignKey(WorkPlan, verbose_name="Перечень работ", on_delete=models.CASCADE, related_name="versions")
    version = models.PositiveIntegerField("№ версии")
    doc_url = models.URLField("URL документа")

    class Meta:
        verbose_name = "Версия перечня работ"
        verbose_name_plural = "Версии перечня работ"
        unique_together = ("plan", "version")
        ordering = ["-version"]

    def __str__(self):
        return f"WP#{self.plan_id} v{self.version}"


class WorkPlanChangeRequest(TimeStampedMixin):
    STATUS = (("pending", "Ожидает"), ("approved", "Принято"), ("rejected", "Отклонено"))
    uuid_wp_change = models.UUIDField("UUID заявки на изменение", default=uuid.uuid4, editable=False)
    plan = models.ForeignKey(WorkPlan, verbose_name="Перечень работ", on_delete=models.CASCADE, related_name="change_requests")
    proposed_doc_url = models.URLField("Предлагаемый документ")
    comment = models.TextField("Комментарий", blank=True)
    status = models.CharField("Статус", max_length=16, choices=STATUS, default="pending")
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="Кто запросил", on_delete=models.PROTECT, related_name="+")
    decided_by = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="Кто принял решение", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        verbose_name = "Заявка на изменение перечня"
        verbose_name_plural = "Заявки на изменения перечня"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Change WP#{self.plan_id} [{self.status}]"


class WorkItemChangeRequest(TimeStampedMixin):
    STATUS_CHOICES = (
        ("pending", "Ожидает"),
        ("approved", "Принято"), 
        ("rejected", "Отклонено"),
        ("edited", "Отредактировано")
    )
    
    uuid_change_request = models.UUIDField("UUID запроса на изменение", default=uuid.uuid4, editable=False)
    work_plan = models.ForeignKey(WorkPlan, verbose_name="Перечень работ", on_delete=models.CASCADE, related_name="item_change_requests")
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="Кто запросил", on_delete=models.PROTECT, related_name="work_item_change_requests")
    decided_by = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="Кто принял решение", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    changes_data = models.JSONField("Данные изменений", default=dict, help_text="JSON с изменениями позиций")
    comment = models.TextField("Комментарий", blank=True)
    status = models.CharField("Статус", max_length=16, choices=STATUS_CHOICES, default="pending")

    old_items_data = models.JSONField("Старые данные позиций", default=list, help_text="JSON с исходными данными позиций")
    new_items_data = models.JSONField("Новые данные позиций", default=list, help_text="JSON с предлагаемыми данными позиций")

    class Meta:
        verbose_name = "Запрос на изменение позиций перечня"
        verbose_name_plural = "Запросы на изменение позиций перечня"
        ordering = ["-created_at"]

    def __str__(self):
        return f"WorkItem Change #{self.id} for WP#{self.work_plan_id} [{self.status}]"
