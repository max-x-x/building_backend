from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from api.models.log import Log, LogLevel, LogCategory


@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    list_display = ('id', 'level_badge', 'category_badge', 'message_short', 'created_at')
    list_filter = ('level', 'category', 'created_at')
    search_fields = ('message',)
    readonly_fields = ('created_at', 'modified_at')
    ordering = ('-created_at',)
    list_per_page = 50
    
    fieldsets = (
        ("📊 Основная информация", {
            "fields": ("level", "category", "message"),
            "classes": ("wide",)
        }),
        ("📅 Даты", {
            "fields": ("created_at", "modified_at"),
            "classes": ("collapse",)
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def level_badge(self, obj):
        colors = {
            LogLevel.DEBUG: "#6c757d",
            LogLevel.INFO: "#17a2b8",
            LogLevel.WARNING: "#ffc107",
            LogLevel.ERROR: "#dc3545",
            LogLevel.CRITICAL: "#6f42c1",
        }
        color = colors.get(obj.level, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_level_display()
        )
    level_badge.short_description = "Уровень"
    level_badge.admin_order_field = "level"

    def category_badge(self, obj):
        colors = {
            LogCategory.AUTH: "#007bff",
            LogCategory.OBJECT: "#28a745",
            LogCategory.DELIVERY: "#ffc107",
            LogCategory.PRESCRIPTION: "#dc3545",
            LogCategory.WORK_PLAN: "#17a2b8",
            LogCategory.ACTIVATION: "#6f42c1",
            LogCategory.USER: "#fd7e14",
            LogCategory.AREA: "#20c997",
            LogCategory.SYSTEM: "#6c757d",
            LogCategory.API: "#e83e8c",
        }
        color = colors.get(obj.category, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            color, obj.get_category_display()
        )
    category_badge.short_description = "Категория"
    category_badge.admin_order_field = "category"

    def message_short(self, obj):
        if len(obj.message) > 100:
            return f"{obj.message[:100]}..."
        return obj.message
    message_short.short_description = "Сообщение"