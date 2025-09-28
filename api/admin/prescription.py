from django.contrib import admin
from api.models.prescription import Prescription, PrescriptionFix

class FixInline(admin.TabularInline):
    model = PrescriptionFix
    extra = 0
    readonly_fields = ("author", "comment", "attachments", "created_at", "modified_at")

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ("id", "object", "author", "title", "requires_stop", "requires_personal_recheck", "status", "created_at", "closed_at")
    list_filter = ("status", "requires_stop", "requires_personal_recheck")
    search_fields = ("object__name", "author__email", "title")
    readonly_fields = ("created_at", "modified_at", "closed_at")
    inlines = [FixInline]
