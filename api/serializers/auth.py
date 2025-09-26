from rest_framework import serializers

from api.serializers.users import UserOutSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class LoginOutSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserOutSerializer()


class RefreshInSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class RefreshOutSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()


class InviteInSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=[c[0] for c in User._meta.get_field("role").choices])


class InviteOutSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    email = serializers.EmailField()
    role = serializers.CharField()


class LogoutInSerializer(serializers.Serializer):
    refresh = serializers.CharField()