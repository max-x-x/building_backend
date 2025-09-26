from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserOutSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "full_name", "phone", "role")


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