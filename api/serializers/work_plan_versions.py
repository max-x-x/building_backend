from rest_framework import serializers
from api.models.work_plan import WorkPlan, WorkPlanVersion


class WPVersionCreateSerializer(serializers.Serializer):
    doc_url = serializers.URLField()

class WPVersionOutSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkPlanVersion
        fields = ("id","uuid_wp_version","version","doc_url","created_at")

class WorkPlanDetailOutSerializer(serializers.ModelSerializer):
    versions = WPVersionOutSerializer(many=True, read_only=True)
    class Meta:
        model = WorkPlan
        fields = ("id","uuid_wp","object","title","created_by","created_at","versions")

class WPChangeRequestCreateSerializer(serializers.Serializer):
    proposed_doc_url = serializers.URLField()
    comment = serializers.CharField(required=False, allow_blank=True)

class WPChangeDecisionSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=["approve","reject"])
    comment = serializers.CharField(required=False, allow_blank=True)
