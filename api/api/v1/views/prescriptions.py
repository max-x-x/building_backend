from django.utils import timezone
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response

from api.api.v1.views.objects import _visible_object_ids_for_user, _paginated
from api.api.v1.views.utils import RoleRequired, send_notification
from api.models.user import Roles
from api.models.prescription import Prescription, PrescriptionFix
# from api.models.notify import Notification  # disabled: notifications handled externally
from api.serializers.prescription import (PrescriptionCreateSerializer, PrescriptionOutSerializer,
                                          PrescriptionFixCreateSerializer, PrescriptionListSerializer)


class PrescriptionsCollectionView(APIView):
    """
    GET  /prescriptions         — список (фильтры те же, что и раньше)
    POST /prescriptions         — создать предписание
    """
    # GET: видят свои объекты. POST: ИКО/ССК/Admin
    def get(self, request):
        object_ids = _visible_object_ids_for_user(request.user)
        qs = Prescription.objects.filter(object_id__in=object_ids).order_by("-created_at")

        # те же фильтры, что были:
        object_id = request.query_params.get("object_id")
        if object_id:
            qs = qs.filter(object_id=object_id)
        status_ = request.query_params.get("status")
        if status_:
            qs = qs.filter(status=status_)
        requires_stop = request.query_params.get("requires_stop")
        if requires_stop in {"1", "true", "True"}:
            qs = qs.filter(requires_stop=True)
        elif requires_stop in {"0", "false", "False"}:
            qs = qs.filter(requires_stop=False)
        author_role = request.query_params.get("author_role")
        if author_role:
            qs = qs.filter(author__role=author_role)

        qs_page, total = _paginated(qs, request)
        data = PrescriptionListSerializer(qs_page, many=True).data
        return Response({"items": data, "total": total}, status=200)

    permission_classes_post = [RoleRequired.as_permitted(Roles.IKO, Roles.SSK, Roles.ADMIN)]
    def post(self, request):
        # ручная проверка прав для POST (чтобы не мешать GET)
        for perm in self.permission_classes_post:
            if not perm().has_permission(request, self):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied()

        ser = PrescriptionCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        pres = Prescription.objects.create(author=request.user, **ser.validated_data)

        if pres.requires_stop:
            pres.object.can_proceed = False
            pres.object.save(update_fields=["can_proceed"])

        # notifications disabled
        return Response(PrescriptionOutSerializer(pres).data, status=201)


class PrescriptionFixView(APIView):
    """
    POST /api/v1/prescriptions/<int:id>/fix
    Кто: Прораб (или admin)
    """
    permission_classes = [RoleRequired.as_permitted(Roles.FOREMAN, Roles.ADMIN)]

    @transaction.atomic
    def post(self, request, id: int):
        try:
            pres = Prescription.objects.select_for_update().get(id=id)
        except Prescription.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)

        if request.user.role != Roles.ADMIN:
            if not pres.object.foreman_id or pres.object.foreman_id != request.user.id:
                return Response({"detail": "Only foreman of this object can fix"}, status=403)

        ser = PrescriptionFixCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        PrescriptionFix.objects.create(prescription=pres, author=request.user, **ser.validated_data)

        pres.status = "awaiting_verification"
        pres.save(update_fields=["status"])
        # notifications disabled
        return Response(PrescriptionOutSerializer(pres).data, status=200)


class PrescriptionVerifyView(APIView):
    """
    POST /api/v1/prescriptions/<int:id>/verify
    Кто: автор предписания (ИКО/ССК) или admin
    Тело: { "accepted": true/false, "comment": "..." }
    """
    permission_classes = [RoleRequired.as_permitted(Roles.IKO, Roles.SSK, Roles.ADMIN)]

    @transaction.atomic
    def post(self, request, id: int):
        try:
            pres = Prescription.objects.select_for_update().get(id=id)
        except Prescription.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)

        if request.user.role != Roles.ADMIN and request.user.id != pres.author_id:
            return Response({"detail": "Only prescription author can verify"}, status=403)

        accepted = request.data.get("accepted", None)
        if accepted is None:
            return Response({"detail": "accepted is required"}, status=400)
        comment = request.data.get("comment", "")

        if accepted:
            pres.status = "closed"
            pres.closed_at = timezone.now()
            pres.save(update_fields=["status", "closed_at"])

            if pres.requires_stop:
                has_active_stoppers = Prescription.objects.filter(object=pres.object, requires_stop=True).exclude(status="closed").exists()
                if not has_active_stoppers:
                    pres.object.can_proceed = True
                    pres.object.save(update_fields=["can_proceed"])
        else:
            # автоклон при отклонении: текущее закрываем и создаём новое открытое
            pres.status = "closed"
            pres.closed_at = timezone.now()
            pres.save(update_fields=["status", "closed_at"])

            new_pres = Prescription.objects.create(
                object=pres.object,
                author=request.user,
                title=pres.title,
                description=f"Повторное нарушение. Причина отклонения: {comment}\n\nПредыдущее описание:\n{pres.description}",
                requires_stop=pres.requires_stop,
                requires_personal_recheck=pres.requires_personal_recheck,
                attachments=pres.attachments,
                status="open",
            )

        # внешние уведомления
        try:
            subj = "Статус нарушения обновлён"
            if accepted:
                msg = f"Нарушение #{pres.id} закрыто."
            else:
                msg = f"Нарушение #{pres.id} отклонено. Создано новое #{new_pres.id}. Причина: {comment}"
            if pres.object.foreman_id and pres.object.foreman:
                send_notification(pres.object.foreman_id, pres.object.foreman.email, subj, msg)
            if pres.object.ssk_id and pres.object.ssk:
                send_notification(pres.object.ssk_id, pres.object.ssk.email, subj, msg)
        except Exception:
            pass

        return Response(PrescriptionOutSerializer(pres).data, status=200)

class ViolationsListView(APIView):
    """
    GET /api/v1/violations?object_id=&only_open=&requires_stop=
    Нарушения = предписания (с возможностью отфильтровать только открытые).
    """
    def get(self, request):
        object_ids = _visible_object_ids_for_user(request.user)

        qs = Prescription.objects.filter(object_id__in=object_ids).order_by("-created_at")

        # фильтры
        object_id = request.query_params.get("object_id")
        if object_id:
            qs = qs.filter(object_id=object_id)

        only_open = request.query_params.get("only_open")
        if only_open in {"1", "true", "True"}:
            qs = qs.exclude(status="closed")

        requires_stop = request.query_params.get("requires_stop")
        if requires_stop in {"1", "true", "True"}:
            qs = qs.filter(requires_stop=True)
        elif requires_stop in {"0", "false", "False"}:
            qs = qs.filter(requires_stop=False)

        qs_page, total = _paginated(qs, request)
        data = PrescriptionListSerializer(qs_page, many=True).data
        return Response({"items": data, "total": total}, status=200)


class PrescriptionsDetailView(APIView):
    """
    GET /api/v1/prescriptions/<int:id>
    Детали предписания (если у пользователя есть доступ к объекту).
    """
    def get(self, request, id: int):
        object_ids = _visible_object_ids_for_user(request.user)
        try:
            pres = Prescription.objects.select_related("object").get(id=id, object_id__in=object_ids)
        except Prescription.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)
        return Response(PrescriptionListSerializer(pres).data, status=200)