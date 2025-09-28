from django.contrib import admin
from api.models.object import ConstructionObject, ObjectActivation


@admin.register(ConstructionObject)
class ConstructionObjectAdmin(admin.ModelAdmin):
    list_display = ("name", "address", "ssk", "foreman", "iko", "can_proceed", "created_at")
    list_filter = ("can_proceed", "ssk", "foreman", "iko")
    search_fields = ("name", "address", "ssk__email", "foreman__email", "iko__email")
    readonly_fields = ("created_at",)


@admin.register(ObjectActivation)
class ObjectActivationAdmin(admin.ModelAdmin):
    list_display = ("id", "object", "status", "requested_by", "requested_at", "iko_checked_at", "approved_at", "created_at")
    list_filter = ("status", "requested_by")
    search_fields = ("object__name", "requested_by__email")
    readonly_fields = ("requested_at", "iko_checked_at", "approved_at", "created_at", "modified_at")
