from rest_framework import serializers
from django.db.models import Count

from api.models.user import User, Roles
from api.models.object import ConstructionObject

class UserBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "full_name", "role")

class ObjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConstructionObject
        fields = ("id", "uuid_obj", "name", "address")

    def create(self, validated_data):
        request = self.context.get("request")
        creator = request.user if request and request.user.is_authenticated else None

        ssk_qs = User.objects.filter(role=Roles.SSK, is_active=True).annotate(
            obj_count=Count("ssk_objects")
        ).order_by("obj_count", "date_joined")
        ssk = ssk_qs.first()
        if not ssk:
            raise serializers.ValidationError({"ssk": "Нет доступных ССК для назначения"})

        obj = ConstructionObject.objects.create(
            ssk=ssk, created_by=creator, **validated_data
        )
        return obj

class ObjectOutSerializer(serializers.ModelSerializer):
    ssk = UserBriefSerializer()
    foreman = UserBriefSerializer(allow_null=True)
    iko = UserBriefSerializer(allow_null=True)

    class Meta:
        model = ConstructionObject
        fields = ("id", "uuid_obj", "name", "address", "ssk", "foreman", "iko", "can_proceed", "created_at")

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
