from django.utils import timezone
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from api.api.v1.views.utils import RoleRequired
from api.models.user import Roles
from api.models.object import ConstructionObject, ObjectActivation
from api.models.notify import Notification
from api.serializers.activation import ActivationRequestInSerializer, ActivationOutSerializer, pick_iko


class ActivationRequestView(APIView):
    """
    POST /api/v1/objects/<int:id>/activation/request
    Кто: ССК объекта или admin
    """
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

        # автопривязка ИКО при необходимости
        if not obj.iko_id:
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

        # уведомления
        Notification.objects.create(object=obj, to_user=obj.iko, type="activation_requested", payload={"activation_id": act.id})
        Notification.objects.create(object=obj, to_role=Roles.IKO, type="visit_action_needed", payload={"hint": "Создайте заявку на посещение"})

        return Response(ActivationOutSerializer(act).data, status=201)


class ActivationIkoCheckView(APIView):
    """
    POST /api/v1/objects/<int:id>/activation/iko-check
    Тело: { "iko_has_violations": bool, "iko_checklist"?, "iko_checklist_pdf"?, "rejected_reason"? }
    Кто: ИКО объекта или admin
    """
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
            # уведомление ССК/прорабу что есть нарушения
            if obj.ssk_id:
                Notification.objects.create(object=obj, to_user=obj.ssk, type="violations_found", payload={})
            if obj.foreman_id:
                Notification.objects.create(object=obj, to_user=obj.foreman, type="violations_found", payload={})
            return Response(ActivationOutSerializer(act).data, status=200)
        else:
            act.status = "approved"
            act.approved_at = timezone.now()
            act.rejected_reason = ""
            act.save()
            obj.can_proceed = True
            obj.save(update_fields=["can_proceed"])
            if obj.ssk_id:
                Notification.objects.create(object=obj, to_user=obj.ssk, type="activation_approved", payload={})
            if obj.foreman_id:
                Notification.objects.create(object=obj, to_user=obj.foreman, type="activation_approved", payload={})
            return Response(ActivationOutSerializer(act).data, status=200)
