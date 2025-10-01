from django.db import transaction, models
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from api.api.v1.views.objects import _visible_object_ids_for_user, _paginated
from api.api.v1.views.utils import RoleRequired
from api.models.user import Roles
from api.models.work_plan import WorkPlanVersion, WorkPlanChangeRequest, WorkPlan, ScheduleItem
from api.serializers.work_plan_versions import (WorkPlanDetailOutSerializer, WPVersionCreateSerializer,
                                                WPChangeRequestCreateSerializer, WPChangeDecisionSerializer)
from api.serializers.work_plans import WorkPlanCreateSerializer, WorkPlanOutSerializer, WorkItemSetStatusSerializer
from api.utils.logging import log_work_plan_created, log_work_item_completed

class WorkPlanCreateView(APIView):
    """
    POST /api/v1/work-plans
    Назначение: ССК объекта прикрепляет перечень работ.
    Побочный эффект: автоматически создаётся расписание из позиций.
    Тело:
    {
      "object_id": "...",
      "title": "ЭС по договору №...",
      "items": [
        {"name": "Подготовка", "quantity": 1, "unit": "этап", "start_date": "2025-10-01", "end_date": "2025-10-03"},
        {"name": "Земляные работы", "quantity": 150, "unit": "м3", "start_date": "2025-10-04", "end_date": "2025-10-10"}
      ]
    }
    """
    def post(self, request):
        ser = WorkPlanCreateSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        plan = ser.save()
        
        # Логируем создание графика работ
        log_work_plan_created(plan.object.name, plan.title, request.user.full_name, request.user.role)
        
        return Response(WorkPlanOutSerializer(plan).data, status=status.HTTP_201_CREATED)

class WorkPlanDetailView(APIView):
    def get(self, request, id: int):
        try:
            wp = WorkPlan.objects.select_related("object","created_by").prefetch_related("items__schedule_item").get(id=id)
        except WorkPlan.DoesNotExist:
            return Response({"detail":"Not found"}, status=404)
        if wp.object_id not in _visible_object_ids_for_user(request.user):
            return Response({"detail":"Forbidden"}, status=403)
        return Response(WorkPlanDetailOutSerializer(wp).data, status=200)

class WorkPlansListView(APIView):
    def get(self, request):
        # Получаем объекты, доступные пользователю
        visible_object_ids = _visible_object_ids_for_user(request.user)
        qs = WorkPlan.objects.filter(object_id__in=visible_object_ids).select_related("object", "created_by").prefetch_related("items__schedule_item").order_by("-created_at")
        
        # Фильтрация по объекту
        object_id = request.query_params.get("object_id")
        if object_id:
            qs = qs.filter(object_id=object_id)
        
        # Поиск по названию объекта или названию графика работ
        query = request.query_params.get("query")
        if query:
            qs = qs.filter(
                Q(object__name__icontains=query) | 
                Q(object__address__icontains=query) | 
                Q(title__icontains=query)
            )
        
        page, total = _paginated(qs, request)
        data = WorkPlanDetailOutSerializer(page, many=True).data
        return Response({"items": data, "total": total}, status=200)

class WorkPlanAddVersionView(APIView):
    permission_classes = [RoleRequired.as_permitted(Roles.SSK, Roles.ADMIN)]

    @transaction.atomic
    def post(self, request, id: int):
        try:
            wp = WorkPlan.objects.select_for_update().get(id=id)
        except WorkPlan.DoesNotExist:
            return Response({"detail":"Not found"}, status=404)
        if request.user.role != Roles.ADMIN and wp.object.ssk_id != request.user.id:
            return Response({"detail":"Forbidden"}, status=403)
        ser = WPVersionCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        next_version = (WorkPlanVersion.objects.filter(plan=wp).aggregate(m=models.Max("version")).get("m") or 0) + 1
        v = WorkPlanVersion.objects.create(plan=wp, version=next_version, doc_url=ser.validated_data["doc_url"])
        return Response({"version": v.version, "doc_url": v.doc_url}, status=201)

class WorkPlanRequestChangeView(APIView):
    permission_classes = [RoleRequired.as_permitted(Roles.FOREMAN, Roles.ADMIN)]

    def post(self, request, id: int):
        try:
            wp = WorkPlan.objects.get(id=id)
        except WorkPlan.DoesNotExist:
            return Response({"detail":"Not found"}, status=404)
        if request.user.role != Roles.ADMIN and wp.object.foreman_id != request.user.id:
            return Response({"detail":"Forbidden"}, status=403)
        ser = WPChangeRequestCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        cr = WorkPlanChangeRequest.objects.create(
            plan=wp, proposed_doc_url=ser.validated_data["proposed_doc_url"],
            comment=ser.validated_data.get("comment",""), requested_by=request.user
        )
        return Response({"status":"pending_review","id":cr.id}, status=202)

class WorkPlanApproveChangeView(APIView):
    permission_classes = [RoleRequired.as_permitted(Roles.SSK, Roles.ADMIN)]

    @transaction.atomic
    def post(self, request, id: int):
        try:
            wp = WorkPlan.objects.select_for_update().get(id=id)
        except WorkPlan.DoesNotExist:
            return Response({"detail":"Not found"}, status=404)
        if request.user.role != Roles.ADMIN and wp.object.ssk_id != request.user.id:
            return Response({"detail":"Forbidden"}, status=403)
        ser = WPChangeDecisionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        decision = ser.validated_data["decision"]
        cr = WorkPlanChangeRequest.objects.filter(plan=wp, status="pending").order_by("created_at").last()
        if not cr:
            return Response({"detail":"Нет активной заявки"}, status=400)
        cr.decided_by = request.user
        if decision == "approve":
            next_version = (WorkPlanVersion.objects.filter(plan=wp).aggregate(m=models.Max("version")).get("m") or 0) + 1
            WorkPlanVersion.objects.create(plan=wp, version=next_version, doc_url=cr.proposed_doc_url)
            cr.status = "approved"
        else:
            cr.status = "rejected"
        cr.save(update_fields=["status","decided_by","updated_at"])
        return Response({"status": cr.status}, status=200)


class WorkItemSetStatusView(APIView):
    permission_classes = [RoleRequired.as_permitted(Roles.SSK, Roles.ADMIN)]

    def post(self, request, id: int):
        try:
            si = ScheduleItem.objects.select_related("object", "work_item", "object__ssk").get(id=id)
        except ScheduleItem.DoesNotExist:
            return Response({"detail":"Not found"}, status=404)
        if request.user.role != Roles.ADMIN and si.object.ssk_id != request.user.id:
            return Response({"detail":"Forbidden: только ССК объекта может изменять статус работ"}, status=403)
        
        ser = WorkItemSetStatusSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        si.status = ser.validated_data["status"]
        si.save(update_fields=["status","modified_at"])
        
        # Логируем завершение работы
        if si.status == "done":
            log_work_item_completed(si.object.name, si.work_item.name, request.user.full_name, request.user.role)
        
        return Response({"status": si.status}, status=200)
