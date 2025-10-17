from rest_framework import serializers
from django.db import transaction
from api.models.work_plan import WorkPlan, WorkItem, ScheduleItem, WorkItemChangeRequest
from api.models.object import ConstructionObject
from api.models.user import Roles
from api.models.area import Area, SubArea
from api.models.delivery import Delivery, Material

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

        created_items = WorkItem.objects.filter(plan=plan)
        
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
    status = serializers.ChoiceField(choices=ScheduleItem.STATUS_CHOICES)
    comment = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        request = self.context["request"]
        schedule_item = self.context["schedule_item"]
        new_status = data["status"]
        current_status = schedule_item.status
        user_role = request.user.role
        
        # Валидация переходов между статусами
        valid_transitions = {
            "planned": ["in_progress"],
            "in_progress": ["completed_foreman", "completed_ssk"],
            "completed_foreman": ["in_progress", "completed_ssk"],
            "completed_ssk": []  # Финальный статус
        }
        
        if new_status not in valid_transitions.get(current_status, []):
            raise serializers.ValidationError(f"Невозможно перейти из статуса '{schedule_item.get_status_display()}' в '{dict(ScheduleItem.STATUS_CHOICES)[new_status]}'")
        
        # Проверка прав доступа
        if new_status == "in_progress":
            if user_role not in [Roles.FOREMAN, Roles.SSK, Roles.ADMIN]:
                raise serializers.ValidationError("Только прораб или ССК могут переводить работу в статус 'В работе'")
            
            # Проверка последовательности работ
            if current_status == "planned":
                # Проверяем, что предыдущие работы завершены ССК
                previous_items = ScheduleItem.objects.filter(
                    object=schedule_item.object,
                    planned_start__lt=schedule_item.planned_start
                ).exclude(status="completed_ssk").exclude(id=schedule_item.id)
                
                if previous_items.exists():
                    raise serializers.ValidationError("Нельзя начать работу, пока предыдущие работы не завершены ССК")
        
        elif new_status == "completed_foreman":
            if user_role not in [Roles.FOREMAN, Roles.ADMIN]:
                raise serializers.ValidationError("Только прораб может завершить работу")
            
            if schedule_item.object.foreman_id != request.user.id and user_role != Roles.ADMIN:
                raise serializers.ValidationError("Прораб может завершать только работы своих объектов")
        
        elif new_status == "completed_ssk":
            if user_role not in [Roles.SSK, Roles.ADMIN]:
                raise serializers.ValidationError("Только ССК может окончательно завершить работу")
            
            if schedule_item.object.ssk_id != request.user.id and user_role != Roles.ADMIN:
                raise serializers.ValidationError("ССК может завершать только работы своих объектов")
        
        return data

class SubAreaBriefSerializer(serializers.ModelSerializer):
    geometry_type = serializers.SerializerMethodField()
    
    class Meta:
        model = SubArea
        fields = ("id", "name", "geometry", "color", "geometry_type", "created_at")
    
    def get_geometry_type(self, obj):
        return obj.get_geometry_type()

class MaterialBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Material
        fields = ("id", "uuid_material", "material_name", "material_quantity", 
                "material_size", "material_volume", "material_netto", "is_confirmed", "created_at")

class DeliveryBriefSerializer(serializers.ModelSerializer):
    materials = MaterialBriefSerializer(many=True, read_only=True)
    
    class Meta:
        model = Delivery
        fields = ("id", "uuid_delivery", "planned_date", "notes", "status", 
                "created_by", "materials", "invoice_photos_folder_url", "created_at", "modified_at")

class WorkItemDetailSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    sub_areas = SubAreaBriefSerializer(many=True, read_only=True)
    deliveries = DeliveryBriefSerializer(many=True, read_only=True)
    
    class Meta:
        model = WorkItem
        fields = ("id", "uuid_wi", "name", "quantity", "unit", "start_date", "end_date", 
                "document_url", "status", "sub_areas", "deliveries", "created_at", "modified_at")
    
    def get_status(self, obj):
        try:
            schedule_item = obj.schedule_item
            return schedule_item.status
        except:
            return "planned"


class WorkItemChangeSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False, allow_null=True, help_text="ID позиции (если не указан - новая позиция)")
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


class WorkPlanChangeRequestSerializer(serializers.Serializer):
    work_plan_id = serializers.IntegerField()
    comment = serializers.CharField(required=False, allow_blank=True)
    items = WorkItemChangeSerializer(many=True, help_text="Новый список позиций перечня работ")

    def validate_work_plan_id(self, value):
        try:
            work_plan = WorkPlan.objects.get(id=value)
        except WorkPlan.DoesNotExist:
            raise serializers.ValidationError("Перечень работ не найден")
        return value

    def validate(self, data):
        request = self.context["request"]
        work_plan_id = data["work_plan_id"]
        
        try:
            work_plan = WorkPlan.objects.get(id=work_plan_id)
        except WorkPlan.DoesNotExist:
            raise serializers.ValidationError("Перечень работ не найден")
        
        if request.user.role not in [Roles.FOREMAN, Roles.SSK, Roles.ADMIN]:
            raise serializers.ValidationError("Недостаточно прав для изменения графика работ")
        
        if request.user.role == Roles.FOREMAN:
            if work_plan.object.foreman_id != request.user.id:
                raise serializers.ValidationError("Прораб может изменять только графики работ своих объектов")
        elif request.user.role == Roles.SSK:
            if work_plan.object.ssk_id != request.user.id:
                raise serializers.ValidationError("ССК может изменять только графики работ своих объектов")
        
        self.context["work_plan"] = work_plan
        return data


class WorkItemChangeRequestOutSerializer(serializers.ModelSerializer):
    requested_by_name = serializers.SerializerMethodField()
    decided_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = WorkItemChangeRequest
        fields = ("id", "uuid_change_request", "work_plan", "requested_by", "requested_by_name",
                 "decided_by", "decided_by_name", "comment", "status", "old_items_data", 
                 "new_items_data", "created_at", "modified_at")
    
    def get_requested_by_name(self, obj):
        return obj.requested_by.full_name if obj.requested_by else None
    
    def get_decided_by_name(self, obj):
        return obj.decided_by.full_name if obj.decided_by else None


class WorkPlanChangeDecisionSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=["approve", "reject", "edit"])
    comment = serializers.CharField(required=False, allow_blank=True)
    edited_items = WorkItemChangeSerializer(many=True, required=False, help_text="Отредактированные позиции (только для decision='edit')")

    def validate(self, data):
        decision = data.get("decision")
        edited_items = data.get("edited_items", [])
        
        if decision == "edit" and not edited_items:
            raise serializers.ValidationError("При редактировании необходимо предоставить отредактированные позиции")
        
        return data


