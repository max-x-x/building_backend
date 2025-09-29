from rest_framework import serializers

from api.models.checklist import DailyChecklist


class DailyChecklistCreateSerializer(serializers.Serializer):
    object_id = serializers.IntegerField()
    data = serializers.JSONField()
    pdf_url = serializers.URLField()
    photos_folder_url = serializers.URLField(required=False, allow_blank=True)

class DailyChecklistPatchSerializer(serializers.Serializer):
    data = serializers.JSONField(required=False)
    pdf_url = serializers.URLField(required=False)
    photos_folder_url = serializers.URLField(required=False, allow_blank=True)

class DailyChecklistOutSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyChecklist
        fields = "__all__"