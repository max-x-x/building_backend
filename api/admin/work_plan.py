from django.contrib import admin
from api.models.work_plan import WorkPlan, WorkItem, ScheduleItem

class WorkItemInline(admin.TabularInline):
    model = WorkItem
    extra = 0

@admin.register(WorkPlan)
class WorkPlanAdmin(admin.ModelAdmin):
    list_display = ("title", "object", "created_by", "created_at")
    list_filter = ("object", "created_by")
    search_fields = ("title", "object__name")
    inlines = [WorkItemInline]
    readonly_fields = ("created_at",)

@admin.register(ScheduleItem)
class ScheduleItemAdmin(admin.ModelAdmin):
    list_display = ("object", "work_item", "planned_start", "planned_end", "status", "created_at")
    list_filter = ("object", "status", "planned_start", "planned_end")
    search_fields = ("object__name", "work_item__name")
    readonly_fields = ("created_at",)
