from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db.models import Q

from api.models.prescription import Prescription
from api.models.object import ConstructionObject
from api.models.user import Roles

User = get_user_model()


class UserOutSerializer(serializers.ModelSerializer):
    violations_total = serializers.SerializerMethodField()
    violations_closed = serializers.SerializerMethodField()
    objects_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ("id", "email", "full_name", "phone", "role", "violations_total", "violations_closed", "objects_count")

    def get_violations_total(self, obj):
        return Prescription.objects.filter(
            Q(object__ssk_id=obj.id) | Q(object__iko_id=obj.id) | Q(object__foreman_id=obj.id)
        ).count()

    def get_violations_closed(self, obj):
        return Prescription.objects.filter(
            Q(object__ssk_id=obj.id) | Q(object__iko_id=obj.id) | Q(object__foreman_id=obj.id),
            status="closed",
        ).count()

    def get_objects_count(self, obj):
        if obj.role == Roles.ADMIN:
            return ConstructionObject.objects.filter(created_by_id=obj.id).count()
        return ConstructionObject.objects.filter(
            Q(ssk_id=obj.id) | Q(iko_id=obj.id) | Q(foreman_id=obj.id)
        ).count()


class UserCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=[c[0] for c in User._meta.get_field("role").choices])
    phone = serializers.CharField(required=False, allow_blank=True)
    full_name = serializers.CharField(required=False, allow_blank=True)


class UserPatchSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    role = serializers.ChoiceField(choices=[c[0] for c in User._meta.get_field("role").choices], required=False)
    phone = serializers.CharField(required=False, allow_blank=True)
    full_name = serializers.CharField(required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)


class UsersListOutSerializer(serializers.Serializer):
    items = UserOutSerializer(many=True)
    total = serializers.IntegerField()