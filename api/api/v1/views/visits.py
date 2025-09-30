from django.db import transaction
from django.utils.dateparse import parse_datetime
from rest_framework.views import APIView
from rest_framework.response import Response

from api.api.v1.views.objects import _visible_object_ids_for_user, _paginated
from api.api.v1.views.utils import RoleRequired
from api.models.user import Roles
from api.models.visit import VisitRequest, QrCode
from api.serializers.visit import (VisitRequestCreateSerializer, VisitRequestOutSerializer, QrOutSerializer,
                                   QrCreateSerializer, VisitRequestListSerializer)
from api.models.notify import Notification


class VisitRequestsView(APIView):
    """
    GET  /visit-requests        — список с фильтрами (mine, period, status, object)
    POST /visit-requests        — создать заявку (ИКО/Admin)
    """
    def get(self, request):
        object_ids = _visible_object_ids_for_user(request.user)
        qs = (VisitRequest.objects
              .filter(object_id__in=object_ids)
              .select_related("object", "requested_by")
              .order_by("-created_at"))

        object_id = request.query_params.get("object_id")
        if object_id:
            qs = qs.filter(object_id=object_id)
        status_ = request.query_params.get("status")
        if status_:
            qs = qs.filter(status=status_)
        mine = request.query_params.get("mine")
        if mine in {"1", "true", "True"}:
            qs = qs.filter(requested_by=request.user)

        # период по planned_at
        from django.utils.dateparse import parse_datetime
        date_from = request.query_params.get("date_from")
        if date_from:
            dt = parse_datetime(date_from)
            if dt:
                qs = qs.filter(planned_at__gte=dt)
        date_to = request.query_params.get("date_to")
        if date_to:
            dt = parse_datetime(date_to)
            if dt:
                qs = qs.filter(planned_at__lte=dt)

        qs_page, total = _paginated(qs, request)
        data = VisitRequestListSerializer(qs_page, many=True).data
        return Response({"items": data, "total": total}, status=200)

    permission_classes_post = [RoleRequired.as_permitted(Roles.IKO, Roles.ADMIN)]
    def post(self, request):
        for perm in self.permission_classes_post:
            if not perm().has_permission(request, self):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied()

        ser = VisitRequestCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        obj = ser.validated_data["object"]

        if request.user.role != Roles.ADMIN and obj.iko_id != request.user.id:
            return Response({"detail": "Only assigned IKO can create visit request"}, status=403)

        vr = VisitRequest.objects.create(
            object=obj,
            requested_by=request.user,
            planned_at=ser.validated_data.get("planned_at"),
            status="pending",
        )
        vr = (
            VisitRequest.objects
            .select_related("object", "requested_by")
            .get(id=vr.id)
        )
        # нотификации оставь как у тебя
        return Response(VisitRequestListSerializer(vr).data, status=201)


class QrCreateView(APIView):
    """
    POST /api/v1/qr-codes
    Кто: admin
    Тело: { object, user, valid_from, valid_to, geojson, visit_request_id? }
    """
    permission_classes = [RoleRequired.as_permitted(Roles.ADMIN)]

    @transaction.atomic
    def post(self, request):
        ser = QrCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        qr = QrCode.objects.create(**ser.validated_data)

        visit_request_id = request.data.get("visit_request_id")
        if visit_request_id:
            try:
                vr = VisitRequest.objects.get(id=visit_request_id, object=qr.object)
                vr.status = "qr_assigned"
                vr.save(update_fields=["status"])
            except VisitRequest.DoesNotExist:
                pass

        Notification.objects.create(object=qr.object, to_user=qr.user, type="qr_assigned", payload={"qr_id": qr.id})
        return Response(QrOutSerializer(qr).data, status=201)


class VisitsDetailView(APIView):
    """
    GET /api/v1/visit-requests/<int:id>
    Детали заявки на посещение (с проверкой доступа).
    """
    def get(self, request, id: int):
        object_ids = _visible_object_ids_for_user(request.user)
        try:
            vr = VisitRequest.objects.select_related("object").get(id=id, object_id__in=object_ids)
        except VisitRequest.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)
        return Response(VisitRequestListSerializer(vr).data, status=200)