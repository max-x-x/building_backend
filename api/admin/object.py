from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from api.models.object import ConstructionObject, ObjectActivation, ObjectRoleAudit, ObjectStatus


@admin.register(ConstructionObject)
class ConstructionObjectAdmin(admin.ModelAdmin):
    list_display = ("name", "address", "status_badge", "ssk", "foreman", "iko", "can_proceed_badge", "created_at")
    list_filter = ("status", "can_proceed", "ssk", "foreman", "iko", "created_at")
    search_fields = ("name", "address", "ssk__email", "foreman__email", "iko__email")
    readonly_fields = ("uuid_obj", "created_at", "modified_at")
    list_per_page = 25
    autocomplete_fields = ("ssk", "foreman", "iko", "created_by")
    
    fieldsets = (
        ("🏗️ Основная информация", {
            "fields": ("name", "address", "status", "can_proceed"),
            "classes": ("wide",)
        }),
        ("👥 Ответственные лица", {
            "fields": ("ssk", "foreman", "iko", "created_by"),
            "classes": ("wide",)
        }),
        ("📁 Документы", {
            "fields": ("folder_url", "document_files", "documents_folder_url"),
            "classes": ("collapse",)
        }),
        ("📅 Системная информация", {
            "fields": ("uuid_obj", "created_at", "modified_at"),
            "classes": ("collapse",)
        }),
    )

    def status_badge(self, obj):
        colors = {
            ObjectStatus.DRAFT: "#6c757d",
            ObjectStatus.ACTIVATION_PENDING: "#ffc107",
            ObjectStatus.ACTIVE: "#28a745",
            ObjectStatus.SUSPENDED: "#dc3545",
            ObjectStatus.COMPLETED_BY_SSK: "#17a2b8",
            ObjectStatus.COMPLETED: "#6f42c1",
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Статус"
    status_badge.admin_order_field = "status"

    def can_proceed_badge(self, obj):
        if obj.can_proceed:
            return format_html('<span style="color: #28a745;">✅ Можно продолжать</span>')
        return format_html('<span style="color: #dc3545;">❌ Остановлено</span>')
    can_proceed_badge.short_description = "Продолжение работ"
    can_proceed_badge.admin_order_field = "can_proceed"


@admin.register(ObjectActivation)
class ObjectActivationAdmin(admin.ModelAdmin):
    list_display = ("object", "status_badge", "requested_by", "requested_at", "iko_checked_at", "approved_at")
    list_filter = ("status", "requested_by", "requested_at")
    search_fields = ("object__name", "requested_by__email")
    readonly_fields = ("uuid_activation", "requested_at", "iko_checked_at", "approved_at", "created_at", "modified_at")
    autocomplete_fields = ("object", "requested_by")
    list_per_page = 25

    fieldsets = (
        ("🏗️ Объект и статус", {
            "fields": ("object", "status"),
            "classes": ("wide",)
        }),
        ("👤 Ответственные", {
            "fields": ("requested_by",),
            "classes": ("wide",)
        }),
        ("📋 Чек-листы", {
            "fields": ("ssk_checklist", "ssk_checklist_pdf", "iko_checklist", "iko_checklist_pdf", "iko_has_violations"),
            "classes": ("collapse",)
        }),
        ("📅 Даты", {
            "fields": ("requested_at", "iko_checked_at", "approved_at"),
            "classes": ("collapse",)
        }),
        ("📝 Комментарии", {
            "fields": ("rejected_reason",),
            "classes": ("collapse",)
        }),
        ("🔧 Системная информация", {
            "fields": ("uuid_activation", "created_at", "modified_at"),
            "classes": ("collapse",)
        }),
    )

    def status_badge(self, obj):
        colors = {
            "pending": "#ffc107",
            "checked": "#dc3545",
            "approved": "#28a745",
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Статус"


@admin.register(ObjectRoleAudit)
class ObjectRoleAuditAdmin(admin.ModelAdmin):
    list_display = ("object", "field", "old_user", "new_user", "changed_by", "created_at")
    list_filter = ("field", "created_at")
    search_fields = ("object__name", "old_user__email", "new_user__email", "changed_by__email")
    readonly_fields = ("uuid_audit", "created_at", "modified_at")
    autocomplete_fields = ("object", "old_user", "new_user", "changed_by")
    list_per_page = 25

    fieldsets = (
        ("🏗️ Объект", {
            "fields": ("object",),
            "classes": ("wide",)
        }),
        ("👥 Изменения ролей", {
            "fields": ("field", "old_user", "new_user", "changed_by"),
            "classes": ("wide",)
        }),
        ("🔧 Системная информация", {
            "fields": ("uuid_audit", "created_at", "modified_at"),
            "classes": ("collapse",)
        }),
    )
