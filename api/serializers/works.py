from rest_framework import serializers

from api.models.work import Work


class WorkCreateSerializer(serializers.Serializer):
    object_id = serializers.IntegerField()
    responsible_id = serializers.UUIDField()
    reviewer_id = serializers.UUIDField()
    title = serializers.CharField(max_length=300)
    status = serializers.ChoiceField(choices=["open","in_progress","done"])

class WorkOutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Work
        fields = ("id","uuid_work","title","status","responsible","reviewer","object","created_at")