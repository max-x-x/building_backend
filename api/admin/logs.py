from django.contrib import admin
from api.models.log import Log


@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    list_display = ('id', 'level', 'category', 'message', 'created_at')
    list_filter = ('level', 'category', 'created_at')
    search_fields = ('message',)
    readonly_fields = ('created_at', 'modified_at')
    ordering = ('-created_at',)
    
    def has_add_permission(self, request):
        return False  # Запрещаем создание логов через админку
    
    def has_change_permission(self, request, obj=None):
        return False  # Запрещаем изменение логов через админку
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser  # Только суперпользователь может удалять логи