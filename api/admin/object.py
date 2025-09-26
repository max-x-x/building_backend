from django.contrib import admin
from api.models.object import ConstructionObject

@admin.register(ConstructionObject)
class ConstructionObjectAdmin(admin.ModelAdmin):
    list_display = ("name", "address", "ssk", "foreman", "iko", "can_proceed", "created_at")
    list_filter = ("can_proceed", "ssk", "foreman", "iko")
    search_fields = ("name", "address", "ssk__email", "foreman__email", "iko__email")
    readonly_fields = ("created_at",)
