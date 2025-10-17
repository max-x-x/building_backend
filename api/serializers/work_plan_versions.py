from rest_framework import serializers
from api.models.work_plan import WorkPlan, WorkPlanVersion, WorkItem, ScheduleItem
from api.models.area import SubArea


class WPVersionCreateSerializer(serializers.Serializer):
    doc_url = serializers.URLField()

class WPVersionOutSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkPlanVersion
        fields = ("id","uuid_wp_version","version","doc_url","created_at")

class SubAreaOutSerializer(serializers.ModelSerializer):
    geometry_type = serializers.SerializerMethodField()
    
    class Meta:
        model = SubArea
        fields = ("id", "name", "geometry", "geometry_type", "color")
    
    def get_geometry_type(self, obj):
        return obj.get_geometry_type()

class WorkItemOutSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    sub_areas = SubAreaOutSerializer(many=True, read_only=True)
    
    class Meta:
        model = WorkItem
        fields = ("id", "uuid_wi", "name", "quantity", "unit", "start_date", "end_date", "document_url", "status", "sub_areas")
    
    def get_status(self, obj):
        try:
            schedule_item = obj.schedule_item
            return schedule_item.status
        except:
            return "planned"


class WorkPlanDetailOutSerializer(serializers.ModelSerializer):
    versions = WPVersionOutSerializer(many=True, read_only=True)
    work_items = WorkItemOutSerializer(source="items", many=True, read_only=True)
    
    class Meta:
        model = WorkPlan
        fields = ("id","uuid_wp","object","title","created_by","created_at","versions","work_items")

class WPChangeRequestCreateSerializer(serializers.Serializer):
    proposed_doc_url = serializers.URLField()
    comment = serializers.CharField(required=False, allow_blank=True)

class WPChangeDecisionSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=["approve","reject"])
    comment = serializers.CharField(required=False, allow_blank=True)
