from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from api.models.prescription import Prescription, PrescriptionFix


class FixInline(admin.TabularInline):
    model = PrescriptionFix
    extra = 0
    readonly_fields = ("author", "comment", "attachments", "created_at", "modified_at")
    fields = ("author", "comment", "attachments", "created_at")
    classes = ("collapse",)


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ("id", "object", "author", "title_short", "status_badge", "requires_stop_badge", "requires_personal_recheck_badge", "created_at", "closed_at")
    list_filter = ("status", "requires_stop", "requires_personal_recheck", "created_at")
    search_fields = ("object__name", "author__email", "title", "description")
    readonly_fields = ("created_at", "modified_at", "closed_at")
    autocomplete_fields = ("object", "author")
    list_per_page = 25
    inlines = [FixInline]

    fieldsets = (
        ("📋 Основная информация", {
            "fields": ("object", "author", "title", "description", "status"),
            "classes": ("wide",)
        }),
        ("⚠️ Требования", {
            "fields": ("requires_stop", "requires_personal_recheck"),
            "classes": ("wide",)
        }),
        ("📎 Вложения", {
            "fields": ("attachments", "violation_photos_folder_url"),
            "classes": ("collapse",)
        }),
        ("📅 Даты", {
            "fields": ("created_at", "closed_at", "modified_at"),
            "classes": ("collapse",)
        }),
    )

    def title_short(self, obj):
        """Сокращенное название нарушения."""
        if len(obj.title) > 50:
            return f"{obj.title[:50]}..."
        return obj.title
    title_short.short_description = "Нарушение"

    def status_badge(self, obj):
        """Отображает статус с цветным бейджем."""
        colors = {
            "open": "#dc3545",              # красный
            "awaiting_verification": "#ffc107", # желтый
            "closed": "#28a745",            # зеленый
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Статус"
    status_badge.admin_order_field = "status"

    def requires_stop_badge(self, obj):
        """Требует остановки работ."""
        if obj.requires_stop:
            return format_html('<span style="color: #dc3545;">🛑 Да</span>')
        return format_html('<span style="color: #28a745;">✅ Нет</span>')
    requires_stop_badge.short_description = "Остановка работ"
    requires_stop_badge.admin_order_field = "requires_stop"

    def requires_personal_recheck_badge(self, obj):
        """Требует личной проверки."""
        if obj.requires_personal_recheck:
            return format_html('<span style="color: #ffc107;">👤 Да</span>')
        return format_html('<span style="color: #6c757d;">❌ Нет</span>')
    requires_personal_recheck_badge.short_description = "Личная проверка"
    requires_personal_recheck_badge.admin_order_field = "requires_personal_recheck"


@admin.register(PrescriptionFix)
class PrescriptionFixAdmin(admin.ModelAdmin):
    list_display = ("prescription", "author", "comment_short", "created_at")
    list_filter = ("created_at",)
    search_fields = ("prescription__title", "author__email", "comment")
    readonly_fields = ("created_at", "modified_at")
    autocomplete_fields = ("prescription", "author")
    list_per_page = 25

    fieldsets = (
        ("📋 Нарушение", {
            "fields": ("prescription",),
            "classes": ("wide",)
        }),
        ("👤 Автор исправления", {
            "fields": ("author",),
            "classes": ("wide",)
        }),
        ("📝 Комментарий", {
            "fields": ("comment",),
            "classes": ("wide",)
        }),
        ("📎 Вложения", {
            "fields": ("attachments", "fix_photos_folder_url"),
            "classes": ("collapse",)
        }),
        ("📅 Даты", {
            "fields": ("created_at", "modified_at"),
            "classes": ("collapse",)
        }),
    )

    def comment_short(self, obj):
        """Сокращенный комментарий."""
        if len(obj.comment) > 100:
            return f"{obj.comment[:100]}..."
        return obj.comment
    comment_short.short_description = "Комментарий"
