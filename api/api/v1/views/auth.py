from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from api.api.v1.views.auth_methods import create_access_token, create_refresh_token, decode_token
from api.api.v1.views.utils import RoleRequired
from api.models.user import RefreshToken, Roles, Invitation
from api.serializers.auth import (LoginSerializer, LoginOutSerializer, RefreshInSerializer, RefreshOutSerializer,
                                  InviteInSerializer, InviteOutSerializer, LogoutInSerializer,
                                  RegisterByInviteInSerializer, RegisterByInviteOutSerializer)

User = get_user_model()


def _client_ip(request):
    xfwd = request.META.get("HTTP_X_FORWARDED_FOR")
    if xfwd:
        return xfwd.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


class AuthLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = LoginSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        email = ser.validated_data["email"].lower()
        password = ser.validated_data["password"]

        try:
            user = User.objects.get(email=email, is_active=True)
        except User.DoesNotExist:
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.check_password(password):
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        access = create_access_token(user)
        refresh, _rt = create_refresh_token(user, user_agent=request.headers.get("User-Agent", ""), ip=_client_ip(request))
        out = LoginOutSerializer({"access": access, "refresh": refresh, "user": user})
        return Response(out.data, status=status.HTTP_200_OK)


class AuthRefreshView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = RefreshInSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        payload = decode_token(ser.validated_data["refresh"])
        if payload.get("type") != "refresh":
            return Response({"detail": "Refresh token required"}, status=401)

        jti = payload.get("jti")
        sub = payload.get("sub")
        try:
            rt = RefreshToken.objects.get(jti=jti, user_id=sub, revoked=False)
        except RefreshToken.DoesNotExist:
            return Response({"detail": "Refresh revoked or not found"}, status=401)

        try:
            user = User.objects.get(id=sub, is_active=True)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=401)

        rt.revoked = True
        rt.save(update_fields=["revoked"])

        access = create_access_token(user)
        new_refresh, _ = create_refresh_token(user, user_agent=request.headers.get("User-Agent", ""), ip=_client_ip(request))
        out = RefreshOutSerializer({"access": access, "refresh": new_refresh})
        return Response(out.data, status=200)


class AuthInviteView(APIView):
    permission_classes = [RoleRequired.as_permitted(Roles.ADMIN)]

    def post(self, request):
        ser = InviteInSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        email = ser.validated_data["email"].lower()
        role = ser.validated_data["role"]

        user, created = User.objects.get_or_create(email=email, defaults={"role": role, "is_active": True})
        if not created and user.role != role:
            user.role = role
            user.save(update_fields=["role"])

        inv = Invitation.objects.create(email=email, role=role, invited_by=request.user)
        # TODO: отправка письма со ссылкой на регистрацию/сброс пароля и inv.token
        out = InviteOutSerializer({"id": user.id, "email": user.email, "role": user.role})
        return Response(out.data, status=201)


class AuthLogoutView(APIView):
    def post(self, request):
        ser = LogoutInSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        payload = decode_token(ser.validated_data["refresh"])
        if payload.get("type") != "refresh":
            return Response({"detail": "Refresh token required"}, status=401)
        jti = payload.get("jti")
        sub = payload.get("sub")
        try:
            rt = RefreshToken.objects.get(jti=jti, user_id=sub, revoked=False)
            rt.revoked = True
            rt.save(update_fields=["revoked"])
        except RefreshToken.DoesNotExist:
            pass
        return Response(status=204)


class AuthRegisterByInviteView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = RegisterByInviteInSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            user = User.objects.get(email=ser.validated_data["email"].lower())
            return Response({"detail": "User already exists"}, status=400)
        except User.DoesNotExist:
            user = User.objects.create(email=ser.validated_data["email"].lower())
        # Обновляем ФИО/телефон и пароль
        user.full_name = ser.validated_data["full_name"]
        user.role = ser.validated_data["role"]
        user.phone = ser.validated_data.get("phone", "")
        user.set_password(ser.validated_data["password1"])
        user.save()

        return Response(RegisterByInviteOutSerializer(user).data, status=status.HTTP_201_CREATED)