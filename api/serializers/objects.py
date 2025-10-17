from rest_framework import serializers
from django.db.models import Count

from api.models.user import User, Roles
from api.models.object import ConstructionObject, ObjectActivation
from api.models.documents import ExecDocument, DocumentFile
from api.models.object import ObjectRoleAudit
from api.models.area import Area, SubArea
from api.models.work_plan import WorkPlan, WorkItem, ScheduleItem
from api.models.delivery import Delivery, Invoice, Material
from api.models.prescription import Prescription, PrescriptionFix
from api.models.work import Work
from api.models.checklist import DailyChecklist

class UserBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "full_name", "role")

class ObjectCreateSerializer(serializers.ModelSerializer):
    document_files = serializers.ListField(
        child=serializers.CharField(), 
        required=False, 
        help_text="Список файлов документов объекта в формате base64"
    )
    
    class Meta:
        model = ConstructionObject
        fields = ("id", "uuid_obj", "name", "address", "document_files")

    def create(self, validated_data):
        request = self.context.get("request")
        creator = request.user if request and request.user.is_authenticated else None

        document_files = validated_data.pop("document_files", [])
        
        obj = ConstructionObject.objects.create(created_by=creator, **validated_data)
        
        if document_files:
            from api.utils.file_storage import upload_object_documents_base64
            
            urls = upload_object_documents_base64(
                document_files, 
                obj.id, 
                obj.name, 
                creator.full_name if creator else "Система", 
                creator.role if creator else "system"
            )
            
            if urls:
                obj.documents_folder_url = urls
                obj.save(update_fields=["documents_folder_url"])
            
        return obj

class SubAreaBriefSerializer(serializers.ModelSerializer):
    geometry_type = serializers.SerializerMethodField()
    
    class Meta:
        model = SubArea
        fields = ("id", "name", "geometry", "geometry_type", "color", "work_item")
    
    def get_geometry_type(self, obj):
        return obj.get_geometry_type()


class AreaBriefSerializer(serializers.ModelSerializer):
    geometry_type = serializers.SerializerMethodField()
    sub_areas = SubAreaBriefSerializer(many=True, read_only=True)
    
    class Meta:
        model = Area
        fields = ("id", "uuid_area", "name", "geometry", "geometry_type", "sub_areas")
    
    def get_geometry_type(self, obj):
        return obj.get_geometry_type()


class ObjectOutSerializer(serializers.ModelSerializer):
    ssk = UserBriefSerializer()
    foreman = UserBriefSerializer(allow_null=True)
    iko = UserBriefSerializer(allow_null=True)
    areas = AreaBriefSerializer(many=True, read_only=True)
    main_polygon = serializers.SerializerMethodField()
    work_progress = serializers.SerializerMethodField()

    class Meta:
        model = ConstructionObject
        fields = ("id", "uuid_obj", "name", "address", "status", "ssk", "foreman", "iko", "can_proceed", "areas", "main_polygon", "work_progress", "documents_folder_url", "created_at")

    def get_work_progress(self, obj):
        try:
            work_plan = WorkPlan.objects.filter(object=obj).order_by('-created_at').first()
            if not work_plan:
                return 0
            
            total_works = WorkItem.objects.filter(plan=work_plan).count()
            if total_works == 0:
                return 0
            
            completed_works = WorkItem.objects.filter(
                plan=work_plan,
                schedule_item__status="done"
            ).count()
            
            return int((completed_works / total_works) * 100)
        except Exception:
            return 0

    def get_main_polygon(self, obj):
        if obj.areas.exists():
            main_area = obj.areas.first()
            return {
                "id": main_area.id,
                "uuid_area": str(main_area.uuid_area),
                "name": main_area.name,
                "geometry": main_area.geometry,
                "geometry_type": main_area.get_geometry_type()
            }
        return None

class ObjectsListOutSerializer(serializers.Serializer):
    items = ObjectOutSerializer(many=True)
    total = serializers.IntegerField()

class ObjectAssignForemanSerializer(serializers.Serializer):
    foreman_id = serializers.UUIDField()

    def validate(self, data):
        obj: ConstructionObject = self.context["object"]
        request = self.context["request"]
        user: User = request.user

        if not (user.role == Roles.ADMIN or user.id == obj.ssk_id):
            raise serializers.ValidationError("Недостаточно прав: назначать прораба может админ или ССК этого объекта")

        try:
            foreman = User.objects.get(id=data["foreman_id"], is_active=True)
        except User.DoesNotExist:
            raise serializers.ValidationError({"foreman_id": "Пользователь не найден"})

        if foreman.role != Roles.FOREMAN:
            raise serializers.ValidationError({"foreman_id": "Пользователь не является прорабом"})

        data["foreman"] = foreman
        return data

    def save(self, **kwargs):
        obj: ConstructionObject = self.context["object"]
        obj.foreman = self.validated_data["foreman"]
        obj.save(update_fields=["foreman"])
        return obj

class ObjectShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConstructionObject
        fields = ("id", "uuid_obj", "name", "address")

class ObjectPatchSerializer(serializers.Serializer):
    foreman_id = serializers.UUIDField(required=False, allow_null=True)
    ssk_id = serializers.UUIDField(required=False, allow_null=True)
    primary_iko_id = serializers.UUIDField(required=False, allow_null=True)
    coordinates_id = serializers.IntegerField(required=False, allow_null=True)
    document_files = serializers.ListField(
        child=serializers.CharField(), 
        required=False, 
        help_text="Список файлов документов объекта в формате base64"
    )
    can_continue_construction = serializers.BooleanField(required=False)

    def validate(self, data):
        obj: ConstructionObject = self.context["object"]
        user: User = self.context["request"].user

        if user.role not in (Roles.ADMIN, Roles.SSK):
            raise serializers.ValidationError("Недостаточно прав")

        def _get_user(uid, role):
            if uid is None:
                return None
            try:
                u = User.objects.get(id=uid, is_active=True)
            except User.DoesNotExist:
                raise serializers.ValidationError({f"{role}_id": "Пользователь не найден"})
            if u.role != role:
                raise serializers.ValidationError({f"{role}_id": f"Пользователь не {role}"})
            return u

        if "foreman_id" in data:
            data["foreman"] = _get_user(data["foreman_id"], Roles.FOREMAN) if data["foreman_id"] else None
        if "ssk_id" in data:
            data["ssk"] = _get_user(data["ssk_id"], Roles.SSK) if data["ssk_id"] else None
        if "primary_iko_id" in data:
            data["iko"] = _get_user(data["primary_iko_id"], Roles.IKO) if data["primary_iko_id"] else None

        return data

    def save(self, **kwargs):
        obj: ConstructionObject = self.context["object"]
        req = self.context["request"]

        old = {"ssk": obj.ssk, "foreman": obj.foreman, "iko": obj.iko}

        if "foreman" in self.validated_data:
            obj.foreman = self.validated_data["foreman"]
        if "ssk" in self.validated_data:
            obj.ssk = self.validated_data["ssk"]
        if "iko" in self.validated_data:
            obj.iko = self.validated_data["iko"]
        if "coordinates_id" in self.validated_data:
            obj.coordinates_id = self.validated_data["coordinates_id"]
        if "can_continue_construction" in self.validated_data:
            obj.can_proceed = bool(self.validated_data["can_continue_construction"])

        document_files = self.validated_data.get("document_files", [])
        if document_files:
            from api.utils.file_storage import upload_object_documents_base64
            
            urls = upload_object_documents_base64(
                document_files, 
                obj.id, 
                obj.name, 
                req.user.full_name, 
                req.user.role
            )
            
            if urls:
                obj.documents_folder_url = urls

        obj.save()

        for field in ("ssk", "foreman", "iko"):
            if old[field] != getattr(obj, field):
                ObjectRoleAudit.objects.create(
                    object=obj, field=field,
                    old_user=old[field], new_user=getattr(obj, field),
                    changed_by=req.user
                )
        return obj


class MaterialDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = Material
        fields = ("id", "uuid_material", "material_name", "material_quantity", 
                "material_size", "material_volume", "material_netto", 
                "is_confirmed", "created_at", "modified_at")

class InvoiceDetailSerializer(serializers.ModelSerializer):
    materials = MaterialDetailSerializer(many=True, read_only=True)
    
    class Meta:
        model = Invoice
        fields = ("id", "uuid_invoice", "pdf_url", "folder_url", "data", 
                "materials", "created_at", "modified_at")

class WorkItemBriefDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkItem
        fields = ("id", "uuid_wi", "name", "quantity", "unit", "start_date", "end_date")

class DeliveryDetailSerializer(serializers.ModelSerializer):
    invoices = InvoiceDetailSerializer(many=True, read_only=True)
    work_item = WorkItemBriefDetailSerializer(read_only=True)
    
    class Meta:
        model = Delivery
        fields = ("id", "uuid_delivery", "work_item", "planned_date", "notes", "status", 
                "created_by", "invoices", "invoice_photos_folder_url", "created_at", "modified_at")

class WorkItemDetailSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    
    class Meta:
        model = WorkItem
        fields = ("id", "uuid_wi", "name", "quantity", "unit", "start_date", 
                "end_date", "document_url", "status", "created_at", "modified_at")
    
    def get_status(self, obj):
        try:
            schedule_item = obj.schedule_item
            return schedule_item.status
        except:
            return "planned"

class WorkPlanDetailSerializer(serializers.ModelSerializer):
    work_items = WorkItemDetailSerializer(source="items", many=True, read_only=True)
    
    class Meta:
        model = WorkPlan
        fields = ("id", "uuid_wp", "title", "created_by", "work_items", 
                "created_at", "modified_at")

class PrescriptionDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prescription
        fields = ("id", "title", "description", "status", "requires_stop", 
                "requires_personal_recheck", "attachments", "violation_photos_folder_url", "author", 
                "created_at", "closed_at", "modified_at")

class PrescriptionFixDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = PrescriptionFix
        fields = ("id", "comment", "attachments", "fix_photos_folder_url", "author", 
                "created_at", "modified_at")

class WorkDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = Work
        fields = ("id", "uuid_work", "title", "status", "responsible", 
                "reviewer", "created_at", "modified_at")

class DailyChecklistDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = DailyChecklist
        fields = ("id", "uuid_checklist", "status", "reviewed_by", 
                "reviewed_at", "created_at", "modified_at")

class ObjectActivationDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = ObjectActivation
        fields = ("id", "uuid_activation", "status", "requested_by", 
                "ssk_checklist", "ssk_checklist_pdf", "requested_at",
                "iko_checklist", "iko_checklist_pdf", "iko_has_violations",
                "iko_checked_at", "approved_at", "rejected_reason",
                "created_at", "modified_at")

class ObjectFullDetailSerializer(serializers.ModelSerializer):
    ssk = UserBriefSerializer(read_only=True)
    foreman = UserBriefSerializer(read_only=True)
    iko = UserBriefSerializer(read_only=True)
    created_by = UserBriefSerializer(read_only=True)
    areas = AreaBriefSerializer(many=True, read_only=True)
    main_polygon = serializers.SerializerMethodField()
    work_progress = serializers.SerializerMethodField()

    deliveries = DeliveryDetailSerializer(many=True, read_only=True)
    work_plans = WorkPlanDetailSerializer(many=True, read_only=True)
    prescriptions = PrescriptionDetailSerializer(many=True, read_only=True)
    works = WorkDetailSerializer(many=True, read_only=True)
    daily_checklists = DailyChecklistDetailSerializer(many=True, read_only=True)
    activations = ObjectActivationDetailSerializer(many=True, read_only=True)

    deliveries_count = serializers.SerializerMethodField()
    work_plans_count = serializers.SerializerMethodField()
    prescriptions_count = serializers.SerializerMethodField()
    open_prescriptions_count = serializers.SerializerMethodField()
    works_count = serializers.SerializerMethodField()
    daily_checklists_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ConstructionObject
        fields = (
            "id", "uuid_obj", "name", "address", "status", "can_proceed",
            "ssk", "foreman", "iko", "created_by", "areas", "main_polygon", "work_progress",
            "documents_folder_url", "created_at", "modified_at",

            "deliveries", "work_plans", "prescriptions", "works", 
            "daily_checklists", "activations",

            "deliveries_count", "work_plans_count", "prescriptions_count",
            "open_prescriptions_count", "works_count", "daily_checklists_count"
        )
    
    def get_work_progress(self, obj):
        try:
            work_plan = WorkPlan.objects.filter(object=obj).order_by('-created_at').first()
            if not work_plan:
                return 0
            
            total_works = WorkItem.objects.filter(plan=work_plan).count()
            if total_works == 0:
                return 0
            
            completed_works = WorkItem.objects.filter(
                plan=work_plan,
                schedule_item__status="done"
            ).count()
            
            return int((completed_works / total_works) * 100)
        except Exception:
            return 0
    
    def get_main_polygon(self, obj):
        if obj.areas.exists():
            main_area = obj.areas.first()
            return {
                "id": main_area.id,
                "uuid_area": str(main_area.uuid_area),
                "name": main_area.name,
                "geometry": main_area.geometry,
                "geometry_type": main_area.get_geometry_type()
            }
        return None
    
    def get_deliveries_count(self, obj):
        return obj.deliveries.count()
    
    def get_work_plans_count(self, obj):
        return obj.work_plans.count()
    
    def get_prescriptions_count(self, obj):
        return obj.prescriptions.count()
    
    def get_open_prescriptions_count(self, obj):
        return obj.prescriptions.filter(status="open").count()
    
    def get_works_count(self, obj):
        return obj.works.count()
    
    def get_daily_checklists_count(self, obj):
        return obj.daily_checklists.count()