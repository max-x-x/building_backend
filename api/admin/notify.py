from django.contrib import admin
from api.models.notify import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "object", "to_user", "to_role", "type", "is_read", "created_at")
    list_filter = ("type", "is_read", "to_role")
    search_fields = ("object__name", "to_user__email", "type")
    readonly_fields = ("created_at", "modified_at")
