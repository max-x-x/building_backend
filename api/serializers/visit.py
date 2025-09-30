from rest_framework import serializers
from api.models.visit import VisitRequest, QrCode
from api.serializers.objects import ObjectShortSerializer
from api.serializers.users import UserOutSerializer


class VisitRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = VisitRequest
        fields = ("object", "planned_at")

class VisitRequestOutSerializer(serializers.ModelSerializer):
    object = ObjectShortSerializer(read_only=True)
    requested_by = UserOutSerializer(read_only=True)

    class Meta:
        model = VisitRequest
        fields = "__all__"

class VisitRequestListSerializer(serializers.ModelSerializer):
    object = ObjectShortSerializer(read_only=True)
    requested_by = UserOutSerializer(read_only=True)

    class Meta:
        model = VisitRequest
        fields = (
            "id", "uuid_visit",
            "object", "requested_by",
            "planned_at", "status",
            "created_at",
        )

class QrCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = QrCode
        fields = ("object", "user", "valid_from", "valid_to", "geojson")

class QrOutSerializer(serializers.ModelSerializer):
    class Meta:
        model = QrCode
        fields = ("id", "uuid_qr", "object", "user", "token", "valid_from", "valid_to", "geojson", "created_at", "updated_at")