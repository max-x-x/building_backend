from rest_framework import serializers

from api.models.checklist import DailyChecklist


class DailyChecklistCreateSerializer(serializers.Serializer):
    object_id = serializers.IntegerField()
    data = serializers.JSONField()
    photos_folder_url = serializers.URLField(required=False, allow_blank=True)

class DailyChecklistPatchSerializer(serializers.Serializer):
    data = serializers.JSONField(required=False)
    photos_folder_url = serializers.URLField(required=False, allow_blank=True)

class DailyChecklistOutSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    reviewed_by_name = serializers.SerializerMethodField()
    object_name = serializers.SerializerMethodField()
    
    class Meta:
        model = DailyChecklist
        fields = "__all__"
    
    def get_author_name(self, obj):
        return obj.author.full_name if obj.author else None
    
    def get_reviewed_by_name(self, obj):
        return obj.reviewed_by.full_name if obj.reviewed_by else None
    
    def get_object_name(self, obj):
        return obj.object.name if obj.object else None


class DailyChecklistListSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    reviewed_by_name = serializers.SerializerMethodField()
    object_name = serializers.SerializerMethodField()
    
    class Meta:
        model = DailyChecklist
        fields = (
            "id", "uuid_daily", "object", "object_name", "author", "author_name",
            "data", "photos_folder_url", "status", "reviewed_by", "reviewed_by_name",
            "reviewed_at", "review_comment", "created_at", "modified_at"
        )
    
    def get_author_name(self, obj):
        return obj.author.full_name if obj.author else None
    
    def get_reviewed_by_name(self, obj):
        return obj.reviewed_by.full_name if obj.reviewed_by else None
    
    def get_object_name(self, obj):
        return obj.object.name if obj.object else None