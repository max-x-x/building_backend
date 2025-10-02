from django.utils import timezone
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response

from api.api.v1.views.utils import RoleRequired, send_notification
from api.models.user import Roles
from api.models.object import ConstructionObject, ObjectActivation, ObjectStatus
from api.serializers.activation import ActivationRequestInSerializer, ActivationOutSerializer, pick_iko
from api.utils.logging import log_activation_requested, log_activation_approved, log_activation_rejected


class ActivationRequestView(APIView):
    permission_classes = [RoleRequired.as_permitted(Roles.ADMIN, Roles.SSK)]

    @transaction.atomic
    def post(self, request, id: int):
        try:
            obj = ConstructionObject.objects.select_for_update().get(id=id)
        except ConstructionObject.DoesNotExist:
            return Response({"detail": "Object not found"}, status=404)

        if request.user.role != Roles.ADMIN and obj.ssk_id != request.user.id:
            return Response({"detail": "Only object SSK can request activation"}, status=403)

        ser = ActivationRequestInSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        if not obj.iko:
            iko = pick_iko()
            if not iko:
                return Response({"detail": "No available IKO"}, status=400)
            obj.iko = iko
            obj.save(update_fields=["iko"])

        act = ObjectActivation.objects.create(
            object=obj,
            status="requested",
            requested_by=request.user,
            ssk_checklist=ser.validated_data.get("ssk_checklist", {}),
            ssk_checklist_pdf=ser.validated_data.get("ssk_checklist_pdf", ""),
        )

        iko_name = obj.iko.full_name if obj.iko else None
        log_activation_requested(obj.name, request.user.full_name, request.user.role, iko_name)

        try:
            if obj.iko_id and obj.iko:
                send_notification(obj.iko_id, obj.iko.email, "Запрос активации объекта", f"Объект '{obj.name}': выберите дату посещения для активации", request.user.full_name, request.user.role)
        except Exception:
            pass

        return Response(ActivationOutSerializer(act).data, status=201)


class ActivationIkoCheckView(APIView):
    permission_classes = [RoleRequired.as_permitted(Roles.IKO, Roles.ADMIN)]

    @transaction.atomic
    def post(self, request, id: int):
        try:
            obj = ConstructionObject.objects.select_for_update().get(id=id)
        except ConstructionObject.DoesNotExist:
            return Response({"detail": "Object not found"}, status=404)

        if request.user.role != Roles.ADMIN and obj.iko_id != request.user.id:
            return Response({"detail": "Only assigned IKO can submit check"}, status=403)

        act = ObjectActivation.objects.filter(object=obj).order_by("-requested_at").first()
        if not act:
            return Response({"detail": "Activation request not found"}, status=400)

        iko_has_violations = bool(request.data.get("iko_has_violations"))
        iko_checklist = request.data.get("iko_checklist") or {}
        iko_checklist_pdf = request.data.get("iko_checklist_pdf", "")
        rejected_reason = request.data.get("rejected_reason", "")

        act.iko_has_violations = iko_has_violations
        act.iko_checklist = iko_checklist
        act.iko_checklist_pdf = iko_checklist_pdf
        act.iko_checked_at = timezone.now()

        if iko_has_violations:
            act.status = "checked"
            act.rejected_reason = rejected_reason
            act.save()
            
            log_activation_rejected(obj.name, request.user.full_name, request.user.role, rejected_reason)
            
            return Response(ActivationOutSerializer(act).data, status=200)
        else:
            act.status = "approved"
            act.approved_at = timezone.now()
            act.rejected_reason = ""
            act.save()
            obj.status = ObjectStatus.ACTIVE
            obj.can_proceed = True
            obj.save(update_fields=["status","can_proceed"])
            
            log_activation_approved(obj.name, request.user.full_name, request.user.role)
            
            try:
                subj = "Активация объекта одобрена"
                msg = f"Объект '{obj.name}' активирован."
                if obj.ssk_id and obj.ssk:
                    send_notification(obj.ssk_id, obj.ssk.email, subj, msg, request.user.full_name, request.user.role)
                if obj.foreman_id and obj.foreman:
                    send_notification(obj.foreman_id, obj.foreman.email, subj, msg, request.user.full_name, request.user.role)
            except Exception:
                pass
            return Response(ActivationOutSerializer(act).data, status=200)
