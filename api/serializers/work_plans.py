from rest_framework import serializers
from django.db import transaction
from api.models.work_plan import WorkPlan, WorkItem, ScheduleItem
from api.models.object import ConstructionObject
from api.models.user import Roles

class WorkItemCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=300)
    quantity = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    unit = serializers.CharField(max_length=32, required=False, allow_blank=True)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    document_url = serializers.URLField(required=False, allow_blank=True)

    def validate(self, data):
        if data["end_date"] < data["start_date"]:
            raise serializers.ValidationError("Дата окончания раньше даты начала")
        return data

class WorkPlanCreateSerializer(serializers.Serializer):
    object_id = serializers.UUIDField()
    title = serializers.CharField(max_length=255, required=False, allow_blank=True)
    items = WorkItemCreateSerializer(many=True)

    def validate(self, data):
        request = self.context["request"]

        try:
            obj = ConstructionObject.objects.get(uuid_obj=data["object_id"])
        except ConstructionObject.DoesNotExist:
            raise serializers.ValidationError({"object_id": "Объект не найден"})

        if not (request.user.role == Roles.ADMIN or request.user.id == obj.ssk_id):
            raise serializers.ValidationError("Недостаточно прав: только админ или ССК объекта может добавить перечень работ")

        self.context["object"] = obj
        return data

    @transaction.atomic
    def create(self, validated_data):
        obj = self.context["object"]
        request = self.context["request"]
        plan = WorkPlan.objects.create(
            object=obj,
            title=validated_data.get("title", ""),
            created_by=request.user,
        )
        items_data = validated_data["items"]
        items = []
        for it in items_data:
            items.append(WorkItem(
                plan=plan,
                name=it["name"],
                quantity=it.get("quantity"),
                unit=it.get("unit", ""),
                start_date=it["start_date"],
                end_date=it["end_date"],
                document_url=it.get("document_url", ""),
            ))
        WorkItem.objects.bulk_create(items)

        sched = [
            ScheduleItem(
                object=obj,
                work_item=wi,
                planned_start=wi.start_date,
                planned_end=wi.end_date,
                status="planned",
            ) for wi in WorkItem.objects.filter(plan=plan)
        ]
        ScheduleItem.objects.bulk_create(sched)
        return plan

class WorkPlanOutSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkPlan
        fields = ("id", "uuid_wp", "object", "title", "created_by", "created_at")
