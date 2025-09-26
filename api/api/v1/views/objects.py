from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from api.models import Roles
from api.serializers.objects import (ObjectCreateSerializer, ObjectOutSerializer, ObjectAssignForemanSerializer,
                                     ObjectsListOutSerializer)
from api.models.object import ConstructionObject

class ObjectsListCreateView(APIView):
    """
    GET  /api/v1/objects   — список объектов
    POST /api/v1/objects   — создать объект (с авто-назначением ССК)
    Доступ:
      - GET: любой аутентифицированный; видимость по роли:
          admin  → все
          ssk    → где он ssk
          iko    → где он iko
          foreman→ где он foreman
      - POST: по бизнес-правилу (обычно admin). Оставлю без жёсткой блокировки, как у тебя было.
    Фильтры GET: ?query=...&limit=20&offset=0
    """
    def get(self, request):
        query = request.query_params.get("query")
        try:
            limit = max(1, min(int(request.query_params.get("limit", 20)), 200))
        except ValueError:
            limit = 20
        try:
            offset = max(0, int(request.query_params.get("offset", 0)))
        except ValueError:
            offset = 0

        role = request.user.role
        qs = ConstructionObject.objects.select_related("ssk", "foreman", "iko").all()

        if role == Roles.SSK:
            qs = qs.filter(ssk=request.user)
        elif role == Roles.IKO:
            qs = qs.filter(iko=request.user)
        elif role == Roles.FOREMAN:
            qs = qs.filter(foreman=request.user)
        # admin видит все

        if query:
            qs = qs.filter(Q(name__icontains=query) | Q(address__icontains=query))

        total = qs.count()
        items = list(qs.order_by("-created_at")[offset: offset + limit])
        out = ObjectsListOutSerializer({"items": items, "total": total}, context={"request": request})
        return Response(out.data, status=200)

    def post(self, request):
        ser = ObjectCreateSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        obj = ser.save()
        return Response(ObjectOutSerializer(obj, context={"request": request}).data, status=status.HTTP_201_CREATED)


class ObjectsAssignForemanView(APIView):
    """
    PATCH /api/v1/objects/{id}
    Назначение: ССК (или admin) назначает прораба на объект.
    Тело: { "foreman_id": "uuid" }
    """
    def patch(self, request, id):
        try:
            obj = ConstructionObject.objects.select_related("ssk", "foreman", "iko").get(uuid_obj=id)
        except ConstructionObject.DoesNotExist:
            return Response({"detail": "Объект не найден"}, status=404)

        ser = ObjectAssignForemanSerializer(data=request.data, context={"request": request, "object": obj})
        ser.is_valid(raise_exception=True)
        obj = ser.save()
        return Response(ObjectOutSerializer(obj).data, status=200)
