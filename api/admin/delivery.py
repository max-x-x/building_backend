from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from api.models.delivery import Delivery, Invoice, Material, LabOrder


class MaterialInline(admin.TabularInline):
    model = Material
    extra = 0
    readonly_fields = ("uuid_material", "created_at", "modified_at")
    fields = ("material_name", "material_quantity", "material_size", "material_volume", "material_netto", "is_confirmed")
    classes = ("collapse",)


class InvoiceInline(admin.TabularInline):
    model = Invoice
    extra = 0
    readonly_fields = ("uuid_invoice", "created_at", "modified_at")
    fields = ("pdf_url", "folder_url", "data")
    classes = ("collapse",)


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ("id", "object", "status_badge", "planned_date", "created_by", "created_at")
    list_filter = ("status", "planned_date", "created_at")
    search_fields = ("object__name", "notes", "created_by__email")
    readonly_fields = ("uuid_delivery", "created_at", "modified_at")
    autocomplete_fields = ("object", "created_by")
    list_per_page = 25
    inlines = [InvoiceInline]

    fieldsets = (
        ("🚚 Основная информация", {
            "fields": ("object", "planned_date", "notes", "status"),
            "classes": ("wide",)
        }),
        ("👤 Ответственные", {
            "fields": ("created_by",),
            "classes": ("wide",)
        }),
        ("🔧 Системная информация", {
            "fields": ("uuid_delivery", "created_at", "modified_at"),
            "classes": ("collapse",)
        }),
    )

    def status_badge(self, obj):
        """Отображает статус поставки с цветным бейджем."""
        colors = {
            "scheduled": "#6c757d",    # серый
            "received": "#ffc107",      # желтый
            "accepted": "#28a745",      # зеленый
            "rejected": "#dc3545",      # красный
            "sent_to_lab": "#17a2b8",   # голубой
            "awaiting_lab": "#6f42c1",  # фиолетовый
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Статус"
    status_badge.admin_order_field = "status"


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("id", "delivery", "object", "pdf_url_short", "folder_url_short", "created_at")
    list_filter = ("created_at",)
    search_fields = ("delivery__object__name", "pdf_url", "folder_url")
    readonly_fields = ("uuid_invoice", "created_at", "modified_at")
    autocomplete_fields = ("object", "delivery")
    list_per_page = 25
    inlines = [MaterialInline]

    fieldsets = (
        ("📄 Основная информация", {
            "fields": ("object", "delivery", "pdf_url", "folder_url"),
            "classes": ("wide",)
        }),
        ("📊 Данные", {
            "fields": ("data",),
            "classes": ("collapse",)
        }),
        ("🔧 Системная информация", {
            "fields": ("uuid_invoice", "created_at", "modified_at"),
            "classes": ("collapse",)
        }),
    )

    def pdf_url_short(self, obj):
        """Сокращенный URL PDF."""
        if obj.pdf_url and len(obj.pdf_url) > 30:
            return f"{obj.pdf_url[:30]}..."
        return obj.pdf_url or "—"
    pdf_url_short.short_description = "PDF URL"

    def folder_url_short(self, obj):
        """Сокращенный URL папки."""
        if obj.folder_url and len(obj.folder_url) > 30:
            return f"{obj.folder_url[:30]}..."
        return obj.folder_url or "—"
    folder_url_short.short_description = "Папка URL"


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ("id", "delivery", "invoice", "material_name", "material_quantity", "is_confirmed_badge", "created_at")
    list_filter = ("is_confirmed", "created_at")
    search_fields = ("material_name", "delivery__object__name")
    readonly_fields = ("uuid_material", "created_at", "modified_at")
    autocomplete_fields = ("delivery", "invoice")
    list_per_page = 25

    fieldsets = (
        ("📦 Основная информация", {
            "fields": ("delivery", "invoice", "material_name"),
            "classes": ("wide",)
        }),
        ("📏 Характеристики", {
            "fields": ("material_quantity", "material_size", "material_volume", "material_netto"),
            "classes": ("wide",)
        }),
        ("✅ Статус", {
            "fields": ("is_confirmed",),
            "classes": ("wide",)
        }),
        ("🔧 Системная информация", {
            "fields": ("uuid_material", "created_at", "modified_at"),
            "classes": ("collapse",)
        }),
    )

    def is_confirmed_badge(self, obj):
        """Статус подтверждения материала."""
        if obj.is_confirmed:
            return format_html('<span style="color: #28a745;">✅ Подтвержден</span>')
        return format_html('<span style="color: #ffc107;">⏳ Ожидает</span>')
    is_confirmed_badge.short_description = "Статус"
    is_confirmed_badge.admin_order_field = "is_confirmed"


@admin.register(LabOrder)
class LabOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "delivery", "status_badge", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("delivery__object__name",)
    readonly_fields = ("uuid_lab_order", "created_at", "modified_at")
    autocomplete_fields = ("delivery",)
    list_per_page = 25

    fieldsets = (
        ("🧪 Основная информация", {
            "fields": ("delivery", "status"),
            "classes": ("wide",)
        }),
        ("📋 Элементы заказа", {
            "fields": ("items",),
            "classes": ("wide",)
        }),
        ("🔧 Системная информация", {
            "fields": ("uuid_lab_order", "created_at", "modified_at"),
            "classes": ("collapse",)
        }),
    )

    def status_badge(self, obj):
        """Отображает статус заказа лаборатории с цветным бейджем."""
        colors = {
            "pending": "#ffc107",    # желтый
            "sent": "#17a2b8",      # голубой
            "completed": "#28a745",  # зеленый
            "failed": "#dc3545",    # красный
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Статус"
    status_badge.admin_order_field = "status"
