from django.utils import timezone
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response

from api.api.v1.views.objects import _visible_object_ids_for_user, _paginated
from api.api.v1.views.utils import RoleRequired, send_notification
from api.models.user import Roles
from api.models.prescription import Prescription, PrescriptionFix
from api.models.notify import Notification
from api.serializers.prescription import (PrescriptionCreateSerializer, PrescriptionOutSerializer,
                                          PrescriptionFixCreateSerializer, PrescriptionListSerializer)
from api.utils.logging import log_prescription_created, log_prescription_fixed, log_prescription_verified


class PrescriptionsCollectionView(APIView):
    def get(self, request):
        object_ids = _visible_object_ids_for_user(request.user)
        qs = Prescription.objects.filter(object_id__in=object_ids).prefetch_related('fixes').order_by("-created_at")

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
        for perm in self.permission_classes_post:
            if not perm().has_permission(request, self):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied()

        ser = PrescriptionCreateSerializer(data=request.data, context={'request': request})
        ser.is_valid(raise_exception=True)
        pres = ser.save(author=request.user)

        if pres.requires_stop:
            pres.object.can_proceed = False
            pres.object.save(update_fields=["can_proceed"])

        log_prescription_created(pres.object.name, pres.title, request.user.full_name, request.user.role)

        try:
            if pres.object.foreman_id and pres.object.foreman:
                sender_role = "ИКО" if request.user.role == Roles.IKO else "ССК"
                send_notification(
                    pres.object.foreman_id,
                    pres.object.foreman.email,
                    "Выявлено нарушение",
                    f"В результате проверки {sender_role} выявлено нарушение '{pres.title}' для объекта '{pres.object.name}'",
                    request.user.full_name,
                    request.user.role
                )
        except Exception:
            pass

        return Response(PrescriptionOutSerializer(pres).data, status=201)


class PrescriptionFixView(APIView):
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

        ser = PrescriptionFixCreateSerializer(data=request.data, context={'request': request})
        ser.is_valid(raise_exception=True)
        prescription_fix = ser.save(prescription=pres, author=request.user)

        pres.status = "awaiting_verification"
        pres.save(update_fields=["status"])
        
        log_prescription_fixed(pres.object.name, pres.title, request.user.full_name, request.user.role)

        try:
            if pres.author_id and pres.author != request.user:
                send_notification(
                    pres.author_id,
                    pres.author.email,
                    "Нарушение исправлено",
                    f"Нарушение '{pres.title}' для объекта '{pres.object.name}' исправлено прорабом",
                    request.user.full_name,
                    request.user.role
                )
        except Exception:
            pass

        return Response(PrescriptionOutSerializer(pres).data, status=200)


class PrescriptionVerifyView(APIView):
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

            log_prescription_verified(pres.object.name, pres.title, request.user.full_name, request.user.role, True)

            if pres.requires_stop:
                has_active_stoppers = Prescription.objects.filter(object=pres.object, requires_stop=True).exclude(status="closed").exists()
                if not has_active_stoppers:
                    pres.object.can_proceed = True
                    pres.object.save(update_fields=["can_proceed"])
        else:
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
            
            log_prescription_verified(pres.object.name, pres.title, request.user.full_name, request.user.role, False, comment)

        try:
            subj = "Статус нарушения обновлён"
            if accepted:
                msg = f"Нарушение #{pres.id} закрыто."
            else:
                msg = f"Нарушение #{pres.id} отклонено. Создано новое #{new_pres.id}. Причина: {comment}"
 
            if pres.object.foreman_id and pres.object.foreman:
                if accepted:
                    foreman_msg = f"Исправление нарушения '{pres.title}' для объекта '{pres.object.name}' принято"
                else:
                    foreman_msg = f"Исправление нарушения '{pres.title}' для объекта '{pres.object.name}' отклонено. Причина: {comment}"
                send_notification(pres.object.foreman_id, pres.object.foreman.email, "Результат проверки исправления", foreman_msg, request.user.full_name, request.user.role)
            
            if pres.object.ssk_id and pres.object.ssk:
                send_notification(pres.object.ssk_id, pres.object.ssk.email, subj, msg, request.user.full_name, request.user.role)
        except Exception:
            pass

        return Response(PrescriptionOutSerializer(pres).data, status=200)

class ViolationsListView(APIView):
    def get(self, request):
        object_ids = _visible_object_ids_for_user(request.user)

        qs = Prescription.objects.filter(object_id__in=object_ids).prefetch_related('fixes').order_by("-created_at")

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
    def get(self, request, id: int):
        object_ids = _visible_object_ids_for_user(request.user)
        try:
            pres = Prescription.objects.select_related("object").prefetch_related('fixes').get(id=id, object_id__in=object_ids)
        except Prescription.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)
        return Response(PrescriptionListSerializer(pres).data, status=200)