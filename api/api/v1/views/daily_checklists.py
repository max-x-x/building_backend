from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response

from api.models.checklist import DailyChecklist
from api.models.user import Roles

from api.api.v1.views.objects import _visible_object_ids_for_user, _paginated
from api.api.v1.views.utils import RoleRequired
from api.models.object import ConstructionObject
from api.serializers.daily_checklists import (DailyChecklistCreateSerializer, DailyChecklistOutSerializer,
                                              DailyChecklistPatchSerializer)


class DailyChecklistsView(APIView):
    def post(self, request):
        if request.user.role not in (Roles.FOREMAN, Roles.ADMIN):
            return Response({"detail":"Forbidden"}, status=403)
        ser = DailyChecklistCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            obj = ConstructionObject.objects.get(id=ser.validated_data["object_id"])
        except ConstructionObject.DoesNotExist:
            return Response({"detail":"Object not found"}, status=404)
        if request.user.role != Roles.ADMIN and obj.foreman_id != request.user.id:
            return Response({"detail":"Only object's foreman can submit"}, status=403)
        dc = DailyChecklist.objects.create(
            object=obj,
            author=request.user,
            data=ser.validated_data["data"],
            photos_folder_url=ser.validated_data.get("photos_folder_url",""),
            status="submitted",
        )
        
        try:
            from api.api.v1.views.utils import send_notification
            if obj.iko_id and obj.iko:
                send_notification(
                    obj.iko_id,
                    obj.iko.email,
                    "Заполнен ежедневный чек-лист",
                    f"Прораб заполнил ежедневный чек-лист для объекта '{obj.name}'",
                    request.user.full_name,
                    request.user.role
                )
            if obj.ssk_id and obj.ssk:
                send_notification(
                    obj.ssk_id,
                    obj.ssk.email,
                    "Заполнен ежедневный чек-лист",
                    f"Прораб заполнил ежедневный чек-лист для объекта '{obj.name}'",
                    request.user.full_name,
                    request.user.role
                )
        except Exception:
            pass
        
        return Response(DailyChecklistOutSerializer(dc).data, status=201)

    def get(self, request):
        object_id = request.query_params.get("object_id")
        status_q = request.query_params.get("status")
        visible = _visible_object_ids_for_user(request.user)
        qs = DailyChecklist.objects.filter(object_id__in=visible).order_by("-created_at")
        if object_id:
            qs = qs.filter(object_id=object_id)
        if status_q:
            qs = qs.filter(status=status_q)
        page, total = _paginated(qs, request)
        return Response({"items": DailyChecklistOutSerializer(page, many=True).data, "total": total}, status=200)

    def patch(self, request):
        if request.user.role not in (Roles.FOREMAN, Roles.ADMIN):
            return Response({"detail":"Forbidden"}, status=403)
        checklist_id = request.query_params.get("id")
        if not checklist_id:
            return Response({"detail":"id is required"}, status=400)
        try:
            dc = DailyChecklist.objects.get(id=checklist_id)
        except DailyChecklist.DoesNotExist:
            return Response({"detail":"Not found"}, status=404)
        if request.user.role != Roles.ADMIN and dc.author_id != request.user.id:
            return Response({"detail":"Forbidden"}, status=403)
        if dc.status != "submitted":
            return Response({"detail":"Нельзя править после ревью"}, status=400)
        ser = DailyChecklistPatchSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        for k,v in ser.validated_data.items():
            setattr(dc, k, v)
        dc.save()
        return Response(DailyChecklistOutSerializer(dc).data, status=200)

class DailyChecklistReviewView(APIView):
    permission_classes = [RoleRequired.as_permitted(Roles.SSK, Roles.ADMIN)]

    def post(self, request, id: int):
        try:
            dc = DailyChecklist.objects.select_related("object").get(id=id)
        except DailyChecklist.DoesNotExist:
            return Response({"detail":"Not found"}, status=404)
        if request.user.role != Roles.ADMIN and dc.object.ssk_id != request.user.id:
            return Response({"detail":"Forbidden"}, status=403)
        decision = request.data.get("decision")
        if decision not in ("approve","reject"):
            return Response({"detail":"decision must be approve|reject"}, status=400)
        dc.status = "approved" if decision=="approve" else "rejected"
        dc.review_comment = request.data.get("comment","")
        dc.reviewed_by = request.user
        dc.reviewed_at = timezone.now()
        dc.save(update_fields=["status","review_comment","reviewed_by","reviewed_at"])
        return Response({"status": dc.status, "reviewed_at": dc.reviewed_at}, status=200)
