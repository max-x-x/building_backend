from rest_framework import serializers
from api.models.prescription import Prescription, PrescriptionFix
from api.serializers.objects import ObjectShortSerializer


class PrescriptionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prescription
        fields = ("object", "title", "description", "requires_stop", "requires_personal_recheck", "attachments")

class PrescriptionOutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prescription
        fields = "__all__"

class PrescriptionFixCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrescriptionFix
        fields = ("comment", "attachments")

class PrescriptionListSerializer(serializers.ModelSerializer):
    object = ObjectShortSerializer(read_only=True)

    class Meta:
        model = Prescription
        fields = (
            "id", "uuid_prescription",
            "object", "author", "title",
            "requires_stop", "requires_personal_recheck", "description",
            "status", "created_at", "closed_at",
        )