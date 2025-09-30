from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from api.models import Roles
from api.serializers.objects import (ObjectCreateSerializer, ObjectOutSerializer, ObjectAssignForemanSerializer,
                                     ObjectsListOutSerializer, ObjectPatchSerializer)
from api.models.object import ConstructionObject, ObjectStatus


def _visible_object_ids_for_user(user):
    """
    Возвращает queryset id объектов, доступных пользователю по роли.
    """
    if user.role == Roles.ADMIN:
        return ConstructionObject.objects.values_list("id", flat=True)

    if user.role == Roles.SSK:
        return ConstructionObject.objects.filter(ssk=user).values_list("id", flat=True)

    if user.role == Roles.IKO:
        return ConstructionObject.objects.filter(iko=user).values_list("id", flat=True)

    # foreman
    return ConstructionObject.objects.filter(foreman=user).values_list("id", flat=True)

def _paginated(qs, request, default_limit=20, max_limit=200):
    try:
        limit = max(1, min(int(request.query_params.get("limit", default_limit)), max_limit))
    except ValueError:
        limit = default_limit
    try:
        offset = max(0, int(request.query_params.get("offset", 0)))
    except ValueError:
        offset = 0
    total = qs.count()
    return qs[offset: offset + limit], total


class ObjectsListCreateView(APIView):
    def get(self, request):
        query = request.query_params.get("query")
        status_param = request.query_params.get("status")
        mine = request.query_params.get("mine")

        qs = ConstructionObject.objects.select_related("ssk", "foreman", "iko").all()

        # видимость по роли
        # SSK теперь видит все объекты; фильтрация по своим — через mine=true
        if request.user.role == Roles.IKO:
            qs = qs.filter(iko=request.user)
        elif request.user.role == Roles.FOREMAN:
            qs = qs.filter(foreman=request.user)
        # admin видит всё

        if status_param:
            qs = qs.filter(status=status_param)
        if query:
            qs = qs.filter(Q(name__icontains=query) | Q(address__icontains=query))
        if mine in {"1", "true", "True"}:
            if request.user.role == Roles.ADMIN:
                qs = qs.filter(created_by=request.user)  # для админа "мои" = я создал
            elif request.user.role == Roles.SSK:
                qs = qs.filter(ssk=request.user)
            elif request.user.role == Roles.IKO:
                qs = qs.filter(iko=request.user)
            elif request.user.role == Roles.FOREMAN:
                qs = qs.filter(foreman=request.user)

        page, total = _paginated(qs.order_by("-created_at"), request)
        return Response(ObjectsListOutSerializer({"items": page, "total": total}).data, status=200)

    def post(self, request):
        if request.user.role != Roles.ADMIN:
            return Response({"detail": "Forbidden"}, status=403)
        ser = ObjectCreateSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        obj = ser.save()
        return Response(ObjectOutSerializer(obj).data, status=status.HTTP_201_CREATED)


class ObjectsDetailView(APIView):
    """
    GET /objects/{id}
    PATCH /objects/{id}
    """
    def get(self, request, id: int):
        try:
            obj = ConstructionObject.objects.select_related("ssk", "foreman", "iko").get(id=id)
        except ConstructionObject.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)

        allowed = (
            request.user.role == Roles.ADMIN or
            request.user.role == Roles.SSK or
            obj.iko_id == request.user.id or
            obj.foreman_id == request.user.id
        )
        if not allowed:
            return Response({"detail": "Forbidden"}, status=403)

        return Response(ObjectOutSerializer(obj).data, status=200)

    def patch(self, request, id: int):
        try:
            obj = ConstructionObject.objects.get(id=id)
        except ConstructionObject.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)

        ser = ObjectPatchSerializer(data=request.data, partial=True, context={"request": request, "object": obj})
        ser.is_valid(raise_exception=True)
        before_ssk = obj.ssk_id
        obj = ser.save()
        # если привязали ССК впервые — статус в ожидание активации
        if not before_ssk and obj.ssk_id and obj.status == ObjectStatus.DRAFT:
            obj.status = ObjectStatus.ACTIVATION_PENDING
            obj.save(update_fields=["status"]) 
        return Response(ObjectOutSerializer(obj).data, status=200)


class ObjectSuspendView(APIView):
    def post(self, request, id: int):
        try:
            obj = ConstructionObject.objects.get(id=id)
        except ConstructionObject.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)

        if request.user.role not in (Roles.IKO, Roles.SSK):
            return Response({"detail": "Forbidden"}, status=403)
        if request.user.role == Roles.SSK and obj.ssk_id != request.user.id:
            return Response({"detail": "Forbidden"}, status=403)
        if request.user.role == Roles.IKO and obj.iko_id != request.user.id:
            return Response({"detail": "Forbidden"}, status=403)

        obj.status = ObjectStatus.SUSPENDED
        obj.can_proceed = False
        obj.save(update_fields=["status", "can_proceed", "modified_at"])
        return Response({"status": obj.status}, status=200)


class ObjectResumeView(APIView):
    def post(self, request, id: int):
        try:
            obj = ConstructionObject.objects.get(id=id)
        except ConstructionObject.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)

        if request.user.role not in (Roles.IKO, Roles.SSK):
            return Response({"detail": "Forbidden"}, status=403)
        if request.user.role == Roles.SSK and obj.ssk_id != request.user.id:
            return Response({"detail": "Forbidden"}, status=403)
        if request.user.role == Roles.IKO and obj.iko_id != request.user.id:
            return Response({"detail": "Forbidden"}, status=403)

        obj.status = ObjectStatus.ACTIVE
        obj.can_proceed = True
        obj.save(update_fields=["status", "can_proceed", "modified_at"])
        return Response({"status": obj.status}, status=200)

class ObjectCompleteView(APIView):
    def post(self, request, id: int):
        try:
            obj = ConstructionObject.objects.get(id=id)
        except ConstructionObject.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)

        if request.user.role != Roles.IKO or obj.iko_id != request.user.id:
            return Response({"detail": "Only assigned IKO can complete"}, status=403)

        obj.status = ObjectStatus.COMPLETED
        obj.can_proceed = False
        obj.save(update_fields=["status", "can_proceed", "modified_at"])
        return Response({"status": obj.status}, status=200)
