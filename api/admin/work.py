from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from api.models.work import Work


@admin.register(Work)
class WorkAdmin(admin.ModelAdmin):
    list_display = ("title", "object", "status_badge", "responsible", "reviewer", "created_at")
    list_filter = ("status", "responsible", "reviewer", "created_at")
    search_fields = ("title", "object__name", "responsible__email", "reviewer__email")
    readonly_fields = ("uuid_work", "created_at", "modified_at")
    autocomplete_fields = ("object", "responsible", "reviewer")
    list_per_page = 25

    fieldsets = (
        ("📋 Основная информация", {
            "fields": ("object", "title", "status"),
            "classes": ("wide",)
        }),
        ("👥 Ответственные", {
            "fields": ("responsible", "reviewer"),
            "classes": ("wide",)
        }),
        ("🔧 Системная информация", {
            "fields": ("uuid_work", "created_at", "modified_at"),
            "classes": ("collapse",)
        }),
    )

    def status_badge(self, obj):
        colors = {
            "pending": "#6c757d",
            "in_progress": "#ffc107",
            "completed": "#28a745",
            "cancelled": "#dc3545",
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Статус"
    status_badge.admin_order_field = "status"
