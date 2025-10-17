from rest_framework import serializers
from django.db import transaction
from api.models.work_plan import WorkPlan, WorkItem, ScheduleItem
from api.models.object import ConstructionObject
from api.models.user import Roles
from api.models.area import Area, SubArea

class SubAreaCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    geometry = serializers.JSONField()
    color = serializers.CharField(max_length=7, default="#FF0000")

    def validate_geometry(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Geometry должен быть объектом")
        geom_type = value.get("type")
        if geom_type not in ["Polygon", "MultiPolygon"]:
            raise serializers.ValidationError("Поддерживаются только Polygon и MultiPolygon")
        return value

class WorkItemCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=300)
    quantity = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    unit = serializers.CharField(max_length=32, required=False, allow_blank=True)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    document_url = serializers.URLField(required=False, allow_blank=True)
    sub_areas = SubAreaCreateSerializer(many=True, required=False)

    def validate(self, data):
        if data["end_date"] < data["start_date"]:
            raise serializers.ValidationError("Дата окончания раньше даты начала")
        return data

class WorkPlanCreateSerializer(serializers.Serializer):
    object_id = serializers.IntegerField()
    title = serializers.CharField(max_length=255, required=False, allow_blank=True)
    items = WorkItemCreateSerializer(many=True)

    def validate(self, data):
        request = self.context["request"]

        try:
            obj = ConstructionObject.objects.get(id=data["object_id"])
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

        # Создаём подполигоны для каждого WorkItem
        created_items = WorkItem.objects.filter(plan=plan)
        
        # Получаем первую область объекта (или создаём если нет)
        area = obj.areas.first()
        if not area:
            area = Area.objects.create(
                name=f"Основная область {obj.name}",
                geometry={"type": "Polygon", "coordinates": []},
                object=obj
            )
        
        for i, it in enumerate(items_data):
            work_item = created_items[i]
            sub_areas_data = it.get("sub_areas", [])
            for sub_area_data in sub_areas_data:
                SubArea.objects.create(
                    name=sub_area_data["name"],
                    geometry=sub_area_data["geometry"],
                    color=sub_area_data["color"],
                    area=area,
                    work_item=work_item,
                )

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

class WorkItemSetStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["planned","in_progress","done"])
