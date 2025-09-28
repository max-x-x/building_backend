from django.db.models import Count
from rest_framework import serializers

from api.models.user import User, Roles
from api.models.object import ObjectActivation


class ActivationRequestInSerializer(serializers.Serializer):
    ssk_checklist = serializers.JSONField(required=False, default=dict)
    ssk_checklist_pdf = serializers.URLField(required=False, allow_blank=True)


class ActivationOutSerializer(serializers.ModelSerializer):
    class Meta:
        model = ObjectActivation
        fields = "__all__"


def pick_iko():
    # ИКО с минимальной загрузкой (по количеству объектов, где он iko)
    return User.objects.filter(role=Roles.IKO, is_active=True).annotate(
        cnt=Count("iko_objects")
    ).order_by("cnt", "date_joined").first()
