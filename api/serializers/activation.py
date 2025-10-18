from django.db.models import Count
from rest_framework import serializers

from api.models.user import User, Roles
from api.models.object import ObjectActivation


class ActivationRequestInSerializer(serializers.Serializer):
    ssk_checklist = serializers.JSONField(required=False, default=dict)
    ssk_checklist_pdf = serializers.URLField(required=False, allow_blank=True)


class ActivationOutSerializer(serializers.ModelSerializer):
    requested_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ObjectActivation
        fields = "__all__"
    
    def get_requested_by_name(self, obj):
        return obj.requested_by.full_name if obj.requested_by else None


class ActivationChecklistSerializer(serializers.ModelSerializer):
    requested_by_name = serializers.SerializerMethodField()
    object_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ObjectActivation
        fields = (
            "id", "uuid_activation", "status", "requested_by", "requested_by_name",
            "ssk_checklist", "ssk_checklist_pdf", "requested_at",
            "iko_checklist", "iko_checklist_pdf", "iko_has_violations",
            "iko_checked_at", "approved_at", "rejected_reason",
            "object_name", "created_at", "modified_at"
        )
    
    def get_requested_by_name(self, obj):
        return obj.requested_by.full_name if obj.requested_by else None
    
    def get_object_name(self, obj):
        return obj.object.name if obj.object else None


def pick_iko():
    return User.objects.filter(role=Roles.IKO, is_active=True).annotate(
        cnt=Count("iko_objects")
    ).order_by("cnt", "date_joined").first()
