from django.db import models
from django.conf import settings
from api.models.timestamp import TimeStampedMixin


class LogLevel(models.TextChoices):
    DEBUG = "debug", "Debug"
    INFO = "info", "Info"
    WARNING = "warning", "Warning"
    ERROR = "error", "Error"
    CRITICAL = "critical", "Critical"


class LogCategory(models.TextChoices):
    AUTH = "auth", "Авторизация"
    OBJECT = "object", "Объекты"
    DELIVERY = "delivery", "Поставки"
    PRESCRIPTION = "prescription", "Нарушения"
    WORK_PLAN = "work_plan", "Графики работ"
    ACTIVATION = "activation", "Активация"
    USER = "user", "Пользователи"
    AREA = "area", "Полигоны"
    SYSTEM = "system", "Система"
    API = "api", "API"


class Log(TimeStampedMixin):
    """
    Модель для хранения логов системы.
    """
    level = models.CharField("Уровень", max_length=10, choices=LogLevel.choices, default=LogLevel.INFO)
    category = models.CharField("Категория", max_length=20, choices=LogCategory.choices, default=LogCategory.SYSTEM)
    message = models.TextField("Подробное сообщение")
    
    class Meta:
        verbose_name = "Лог"
        verbose_name_plural = "Логи"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["level"]),
            models.Index(fields=["category"]),
            models.Index(fields=["created_at"]),
        ]
    
    def __str__(self):
        return f"[{self.level.upper()}] {self.category}: {self.message[:50]}"
    
    @classmethod
    def create_log(cls, level, category, message):
        """Создает новый лог с переданными параметрами."""
        return cls.objects.create(
            level=level,
            category=category,
            message=message
        )
