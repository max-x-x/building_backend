import uuid
from django.db import models
from api.models.timestamp import TimeStampedMixin
from api.models.work_plan import WorkItem


class Area(TimeStampedMixin):
    uuid_area = models.UUIDField("UUID области", default=uuid.uuid4, editable=False)
    name = models.CharField("Название области", max_length=255)
    geometry = models.JSONField("GeoJSON geometry", help_text="Polygon или MultiPolygon в формате GeoJSON")
    object = models.ForeignKey(
        "ConstructionObject", 
        verbose_name="Объект строительства",
        on_delete=models.CASCADE, 
        related_name="areas",
        null=True, 
        blank=True
    )
    
    class Meta:
        verbose_name = "Область/полигон"
        verbose_name_plural = "Области/полигоны"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.name} ({self.get_geometry_type()})"
    
    def get_geometry_type(self):
        return self.geometry.get("type", "Unknown") if self.geometry else "Empty"


class SubArea(TimeStampedMixin):
    name = models.CharField("Название подобласти/подполигона", max_length=255)
    geometry = models.JSONField("GeoJSON geometry", help_text="Polygon или MultiPolygon в формате GeoJSON")
    color = models.CharField("Цвет", max_length=7, default="#FF0000", help_text="HEX цвет, например #RRGGBB")
    area = models.ForeignKey(
        Area,
        verbose_name="Родительская область",
        on_delete=models.CASCADE,
        related_name="sub_areas",
    )
    work_item = models.ForeignKey(
        WorkItem,
        verbose_name="Позиция перечня работ",
        on_delete=models.SET_NULL,
        related_name="sub_areas",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Подобласть/подполигон"
        verbose_name_plural = "Подобласти/подполигоны"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.get_geometry_type()})"

    def get_geometry_type(self):
        return self.geometry.get("type", "Unknown") if self.geometry else "Empty"
