from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from api.models.area import Area


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ("name", "object", "geometry_type_badge", "created_at")
    list_filter = ("object", "created_at")
    search_fields = ("name", "object__name")
    readonly_fields = ("uuid_area", "created_at", "modified_at")
    autocomplete_fields = ("object",)
    list_per_page = 25

    fieldsets = (
        ("📍 Основная информация", {
            "fields": ("name", "object"),
            "classes": ("wide",)
        }),
        ("🗺️ Геометрия", {
            "fields": ("geometry",),
            "classes": ("wide",)
        }),
        ("🔧 Системная информация", {
            "fields": ("uuid_area", "created_at", "modified_at"),
            "classes": ("collapse",)
        }),
    )

    def geometry_type_badge(self, obj):
        geometry_type = obj.get_geometry_type()
        colors = {
            "Polygon": "#28a745",
            "MultiPolygon": "#17a2b8",
            "Point": "#ffc107",
            "LineString": "#007bff",
        }
        color = colors.get(geometry_type, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color, geometry_type
        )
    geometry_type_badge.short_description = "Тип геометрии"
    geometry_type_badge.admin_order_field = "geometry__type"
