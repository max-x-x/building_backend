from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from api.models.memo import Memo


@admin.register(Memo)
class MemoAdmin(admin.ModelAdmin):
    list_display = ("title", "pdf_url_short", "created_at")
    list_filter = ("created_at",)
    search_fields = ("title", "pdf_url")
    readonly_fields = ("uuid_memo", "created_at", "modified_at")
    list_per_page = 25

    fieldsets = (
        ("📝 Основная информация", {
            "fields": ("title", "pdf_url"),
            "classes": ("wide",)
        }),
        ("🔧 Системная информация", {
            "fields": ("uuid_memo", "created_at", "modified_at"),
            "classes": ("collapse",)
        }),
    )

    def pdf_url_short(self, obj):
        """Сокращенный URL PDF."""
        if obj.pdf_url and len(obj.pdf_url) > 50:
            return f"{obj.pdf_url[:50]}..."
        return obj.pdf_url or "—"
    pdf_url_short.short_description = "PDF URL"
