from secrets import token_urlsafe
from uuid import UUID

from django.db.models import Q
from rest_framework.response import Response
from rest_framework.views import APIView

from api.api.v1.views.utils import RoleRequired
from api.models.user import Roles, User
from api.serializers.users import UserOutSerializer, UserPatchSerializer, UserCreateSerializer, UsersListOutSerializer
from api.utils.logging import log_user_created, log_user_updated


class UsersMeView(APIView):
    def get(self, request):
        ser = UserOutSerializer(request.user)
        return Response(ser.data, status=200)


class UsersDetailView(APIView):
    """
    GET /users/{id}
    PATCH /users/{id}
    """
    def get(self, request, id: UUID):
        # базовое правило: admin/sysadmin или self
        if str(request.user.id) != str(id) and request.user.role != Roles.ADMIN:
            return Response({"detail": "Forbidden"}, status=403)
        try:
            user = User.objects.get(id=id)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=404)
        return Response(UserOutSerializer(user).data, status=200)

    def patch(self, request, id: UUID):
        try:
            user = User.objects.get(id=id)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=404)

        # права: admin/sysadmin — всё; self — только контакты
        is_self = str(request.user.id) == str(id)
        if not is_self and request.user.role != Roles.ADMIN:
            return Response({"detail": "Forbidden"}, status=403)

        ser = UserPatchSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        if is_self and request.user.role != Roles.ADMIN:
            # self может менять только контакты
            data = {k: v for k, v in data.items() if k in {"full_name", "phone"}}

        if "role" in data and request.user.role != Roles.ADMIN:
            return Response({"detail": "Cannot change role"}, status=403)

        for k, v in data.items():
            setattr(user, k, v)
        user.save()
        
        # Логируем изменение пользователя
        log_user_updated(user.full_name, user.email, user.role, request.user.full_name, request.user.role)
        
        return Response(UserOutSerializer(user).data, status=200)


class UsersListCreateView(APIView):
    permission_classes = [RoleRequired.as_permitted(Roles.ADMIN)]

    def get(self, request):
        role = request.query_params.get("role")
        query = request.query_params.get("query")
        try:
            limit = max(1, min(int(request.query_params.get("limit", 20)), 200))
        except ValueError:
            limit = 20
        try:
            offset = max(0, int(request.query_params.get("offset", 0)))
        except ValueError:
            offset = 0

        qs = User.objects.all().order_by("-date_joined")
        if role:
            qs = qs.filter(role=role)
        if query:
            qs = qs.filter(Q(email__icontains=query) | Q(full_name__icontains=query) | Q(phone__icontains=query))

        total = qs.count()
        users = list(qs[offset: offset + limit])
        out = UsersListOutSerializer({"items": users, "total": total})
        return Response(out.data, status=200)

    def post(self, request):
        ser = UserCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        email = ser.validated_data["email"].lower()
        role = ser.validated_data["role"]
        phone = ser.validated_data.get("phone", "")
        full_name = ser.validated_data.get("full_name", "")

        temp_password = token_urlsafe(12)
        user = User.objects.create_user(
            email=email,
            password=temp_password,
            role=role,
            phone=phone,
            full_name=full_name,
            is_active=True,
        )
        
        # Логируем создание пользователя
        log_user_created(user.full_name, user.email, user.role, request.user.full_name, request.user.role)
        
        return Response(UserOutSerializer(user).data, status=201)
