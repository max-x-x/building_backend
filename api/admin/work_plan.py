from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from api.models.work_plan import WorkPlan, WorkItem, ScheduleItem


class WorkItemInline(admin.TabularInline):
    model = WorkItem
    extra = 0
    readonly_fields = ("uuid_wi", "created_at", "modified_at")
    fields = ("name", "quantity", "unit", "start_date", "end_date", "document_url")
    classes = ("collapse",)


@admin.register(WorkPlan)
class WorkPlanAdmin(admin.ModelAdmin):
    list_display = ("title", "object", "created_by", "work_items_count", "created_at")
    list_filter = ("object", "created_by", "created_at")
    search_fields = ("title", "object__name")
    readonly_fields = ("uuid_wp", "created_at", "modified_at")
    autocomplete_fields = ("object", "created_by")
    list_per_page = 25
    inlines = [WorkItemInline]

    fieldsets = (
        ("📋 Основная информация", {
            "fields": ("object", "title", "created_by"),
            "classes": ("wide",)
        }),
        ("🔧 Системная информация", {
            "fields": ("uuid_wp", "created_at", "modified_at"),
            "classes": ("collapse",)
        }),
    )

    def work_items_count(self, obj):
        count = obj.items.count()
        return format_html('<span style="background-color: #007bff; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">{}</span>', count)
    work_items_count.short_description = "Работ"
    work_items_count.admin_order_field = "items__count"


@admin.register(WorkItem)
class WorkItemAdmin(admin.ModelAdmin):
    list_display = ("name", "plan", "quantity", "unit", "start_date", "end_date", "status_from_schedule")
    list_filter = ("plan__object", "start_date", "end_date")
    search_fields = ("name", "plan__title", "plan__object__name")
    readonly_fields = ("uuid_wi", "created_at", "modified_at")
    autocomplete_fields = ("plan",)
    list_per_page = 25

    fieldsets = (
        ("📋 Основная информация", {
            "fields": ("plan", "name"),
            "classes": ("wide",)
        }),
        ("📏 Характеристики", {
            "fields": ("quantity", "unit"),
            "classes": ("wide",)
        }),
        ("📅 Даты", {
            "fields": ("start_date", "end_date"),
            "classes": ("wide",)
        }),
        ("📄 Документы", {
            "fields": ("document_url",),
            "classes": ("collapse",)
        }),
        ("🔧 Системная информация", {
            "fields": ("uuid_wi", "created_at", "modified_at"),
            "classes": ("collapse",)
        }),
    )

    def status_from_schedule(self, obj):
        try:
            schedule_item = obj.schedule_item
            colors = {
                "planned": "#6c757d",
                "in_progress": "#ffc107",
                "done": "#28a745",
            }
            color = colors.get(schedule_item.status, "#6c757d")
            return format_html(
                '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
                color, schedule_item.get_status_display()
            )
        except:
            return format_html('<span style="color: #6c757d;">—</span>')
    status_from_schedule.short_description = "Статус"


@admin.register(ScheduleItem)
class ScheduleItemAdmin(admin.ModelAdmin):
    list_display = ("object", "work_item", "planned_start", "planned_end", "status_badge", "created_at")
    list_filter = ("object", "status", "planned_start", "planned_end", "created_at")
    search_fields = ("object__name", "work_item__name")
    readonly_fields = ("created_at", "modified_at")
    autocomplete_fields = ("object", "work_item")
    list_per_page = 25

    fieldsets = (
        ("🏗️ Объект и работа", {
            "fields": ("object", "work_item"),
            "classes": ("wide",)
        }),
        ("📅 Планируемые даты", {
            "fields": ("planned_start", "planned_end"),
            "classes": ("wide",)
        }),
        ("📊 Статус", {
            "fields": ("status",),
            "classes": ("wide",)
        }),
        ("📅 Системная информация", {
            "fields": ("created_at", "modified_at"),
            "classes": ("collapse",)
        }),
    )

    def status_badge(self, obj):
        colors = {
            "planned": "#6c757d",
            "in_progress": "#ffc107",
            "done": "#28a745",
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Статус"
    status_badge.admin_order_field = "status"
