from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from api.models.checklist import DailyChecklist


@admin.register(DailyChecklist)
class DailyChecklistAdmin(admin.ModelAdmin):
    list_display = ("object", "author", "status_badge", "reviewed_by", "reviewed_at", "created_at")
    list_filter = ("status", "author", "reviewed_by", "created_at")
    search_fields = ("object__name", "author__email", "reviewed_by__email")
    readonly_fields = ("uuid_daily", "created_at", "modified_at", "reviewed_at")
    autocomplete_fields = ("object", "author", "reviewed_by")
    list_per_page = 25

    fieldsets = (
        ("📋 Основная информация", {
            "fields": ("object", "author", "status"),
            "classes": ("wide",)
        }),
        ("📊 Данные чек-листа", {
            "fields": ("data",),
            "classes": ("wide",)
        }),
        ("📄 Документы", {
            "fields": ("photos_folder_url",),
            "classes": ("collapse",)
        }),
        ("👤 Проверка", {
            "fields": ("reviewed_by", "reviewed_at", "review_comment"),
            "classes": ("collapse",)
        }),
        ("🔧 Системная информация", {
            "fields": ("uuid_daily", "created_at", "modified_at"),
            "classes": ("collapse",)
        }),
    )

    def status_badge(self, obj):
        colors = {
            "submitted": "#ffc107",
            "approved": "#28a745",
            "rejected": "#dc3545",
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Статус"
    status_badge.admin_order_field = "status"
