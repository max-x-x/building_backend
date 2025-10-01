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
        return False  # Запрещаем создание логов через админку
    
    def has_change_permission(self, request, obj=None):
        return False  # Запрещаем изменение логов через админку
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser  # Только суперпользователь может удалять логи

    def level_badge(self, obj):
        """Отображает уровень лога с цветным бейджем."""
        colors = {
            LogLevel.DEBUG: "#6c757d",      # серый
            LogLevel.INFO: "#17a2b8",       # голубой
            LogLevel.WARNING: "#ffc107",    # желтый
            LogLevel.ERROR: "#dc3545",      # красный
            LogLevel.CRITICAL: "#6f42c1",  # фиолетовый
        }
        color = colors.get(obj.level, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_level_display()
        )
    level_badge.short_description = "Уровень"
    level_badge.admin_order_field = "level"

    def category_badge(self, obj):
        """Отображает категорию лога с цветным бейджем."""
        colors = {
            LogCategory.AUTH: "#007bff",           # синий
            LogCategory.OBJECT: "#28a745",        # зеленый
            LogCategory.DELIVERY: "#ffc107",      # желтый
            LogCategory.PRESCRIPTION: "#dc3545",  # красный
            LogCategory.WORK_PLAN: "#17a2b8",     # голубой
            LogCategory.ACTIVATION: "#6f42c1",   # фиолетовый
            LogCategory.USER: "#fd7e14",          # оранжевый
            LogCategory.AREA: "#20c997",          # бирюзовый
            LogCategory.SYSTEM: "#6c757d",        # серый
            LogCategory.API: "#e83e8c",           # розовый
        }
        color = colors.get(obj.category, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            color, obj.get_category_display()
        )
    category_badge.short_description = "Категория"
    category_badge.admin_order_field = "category"

    def message_short(self, obj):
        """Сокращенное сообщение лога."""
        if len(obj.message) > 100:
            return f"{obj.message[:100]}..."
        return obj.message
    message_short.short_description = "Сообщение"