from rest_framework import serializers
from django.db.models import Count

from api.models.user import User, Roles
from api.models.object import ConstructionObject
from api.models.documents import ExecDocument, DocumentFile
from api.models.area import Area
from api.models.work_plan import WorkPlan, WorkItem, ScheduleItem

class UserBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "full_name", "role")

class ObjectCreateSerializer(serializers.ModelSerializer):
    # ссылки на файлы/папку из файлового хранилища
    folder_url = serializers.URLField(required=False, allow_blank=True)
    document_files = serializers.ListField(child=serializers.URLField(), required=False)
    class Meta:
        model = ConstructionObject
        fields = ("id", "uuid_obj", "name", "address", "folder_url", "document_files")

    def create(self, validated_data):
        request = self.context.get("request")
        creator = request.user if request and request.user.is_authenticated else None

        folder_url = validated_data.pop("folder_url", "")
        document_files = validated_data.pop("document_files", [])
        obj = ConstructionObject.objects.create(created_by=creator, **validated_data)
        # сохранить ссылки на документы
        if folder_url:
            ExecDocument.objects.create(object=obj, kind="general", pdf_url=folder_url, created_by=creator)
        for url in document_files:
            DocumentFile.objects.create(object=obj, name=url.rsplit("/", 1)[-1], url=url)
        return obj

class AreaBriefSerializer(serializers.ModelSerializer):
    """Краткий сериализатор для полигона объекта."""
    geometry_type = serializers.SerializerMethodField()
    
    class Meta:
        model = Area
        fields = ("id", "uuid_area", "name", "geometry", "geometry_type")
    
    def get_geometry_type(self, obj):
        return obj.get_geometry_type()


class ObjectOutSerializer(serializers.ModelSerializer):
    ssk = UserBriefSerializer()
    foreman = UserBriefSerializer(allow_null=True)
    iko = UserBriefSerializer(allow_null=True)
    areas = AreaBriefSerializer(many=True, read_only=True)
    work_progress = serializers.SerializerMethodField()

    class Meta:
        model = ConstructionObject
        fields = ("id", "uuid_obj", "name", "address", "status", "ssk", "foreman", "iko", "can_proceed", "areas", "work_progress", "created_at")

    def get_work_progress(self, obj):
        """Рассчитывает процент выполнения работ по графику."""
        try:
            # Получаем последний график работ для объекта
            work_plan = WorkPlan.objects.filter(object=obj).order_by('-created_at').first()
            if not work_plan:
                return 0
            
            # Считаем общее количество работ
            total_works = WorkItem.objects.filter(plan=work_plan).count()
            if total_works == 0:
                return 0
            
            # Считаем выполненные работы (статус "done")
            completed_works = WorkItem.objects.filter(
                plan=work_plan,
                schedule_item__status="done"
            ).count()
            
            # Возвращаем процент
            return int((completed_works / total_works) * 100)
        except Exception:
            return 0

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
    folder_url = serializers.URLField(required=False, allow_blank=True)
    document_files = serializers.ListField(child=serializers.URLField(), required=False)
    can_continue_construction = serializers.BooleanField(required=False)

    def validate(self, data):
        obj: ConstructionObject = self.context["object"]
        user: User = self.context["request"].user

        # admin — везде; ССК — может работать с любым объектом (назначать себя и других)
        if user.role not in (Roles.ADMIN, Roles.SSK):
            raise serializers.ValidationError("Недостаточно прав")

        # проверить роли, если переданы
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
        from api.models.object import ObjectRoleAudit
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

        obj.save()

        # документы
        folder_url = self.validated_data.get("folder_url")
        if folder_url:
            ExecDocument.objects.create(object=obj, kind="general", pdf_url=folder_url, created_by=req.user)
        for url in self.validated_data.get("document_files", []) or []:
            DocumentFile.objects.create(object=obj, name=url.rsplit("/", 1)[-1], url=url)

        # аудит смен ролей
        for field in ("ssk", "foreman", "iko"):
            if old[field] != getattr(obj, field):
                ObjectRoleAudit.objects.create(
                    object=obj, field=field,
                    old_user=old[field], new_user=getattr(obj, field),
                    changed_by=req.user
                )
        return obj