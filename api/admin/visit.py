from django.contrib import admin
from api.models.visit import VisitRequest, QrCode


@admin.register(VisitRequest)
class VisitRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "object", "requested_by", "planned_at", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("object__name", "requested_by__email")
    readonly_fields = ("created_at", "modified_at")


@admin.register(QrCode)
class QrCodeAdmin(admin.ModelAdmin):
    list_display = ("id", "object", "user", "token", "valid_from", "valid_to", "created_at")
    list_filter = ("object", "user")
    search_fields = ("object__name", "user__email", "token")
    readonly_fields = ("token", "created_at", "modified_at")