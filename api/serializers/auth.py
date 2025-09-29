from rest_framework import serializers

from api.models.user import Invitation
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


class RegisterByInviteInSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    email = serializers.EmailField()
    full_name = serializers.CharField(max_length=200)
    phone = serializers.CharField(required=False, allow_blank=True)
    password1 = serializers.CharField(min_length=8)
    password2 = serializers.CharField(min_length=8)

    def validate(self, data):
        if data["password1"] != data["password2"]:
            raise serializers.ValidationError({"password2": "Пароли не совпадают"})
        try:
            inv = Invitation.objects.get(token=data["token"], email__iexact=data["email"])
        except Invitation.DoesNotExist:
            raise serializers.ValidationError({"token": "Неверный токен или email"})
        if inv.is_expired():
            raise serializers.ValidationError({"token": "Срок действия приглашения истёк"})
        if inv.accepted_at:
            raise serializers.ValidationError({"token": "Приглашение уже принято"})
        self.context["invitation"] = inv
        return data

class RegisterByInviteOutSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "full_name", "phone", "role")