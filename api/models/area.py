import uuid
from django.db import models
from api.models.timestamp import TimeStampedMixin


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
