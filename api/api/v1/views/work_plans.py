from django.db import transaction, models
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from api.api.v1.views.objects import _visible_object_ids_for_user, _paginated
from api.api.v1.views.utils import RoleRequired
from api.models.user import Roles
from api.models.work_plan import WorkPlanVersion, WorkPlanChangeRequest, WorkPlan, WorkItem, ScheduleItem, WorkItemChangeRequest
from api.serializers.work_plan_versions import (WorkPlanDetailOutSerializer, WPVersionCreateSerializer,
                                                WPChangeRequestCreateSerializer, WPChangeDecisionSerializer)
from api.serializers.work_plans import (WorkPlanCreateSerializer, WorkPlanOutSerializer, WorkItemSetStatusSerializer, 
                                        WorkItemDetailSerializer, WorkPlanChangeRequestSerializer, 
                                        WorkItemChangeRequestOutSerializer, WorkPlanChangeDecisionSerializer)
from api.utils.logging import log_work_plan_created, log_work_item_completed

class WorkPlanCreateView(APIView):
    def post(self, request):
        ser = WorkPlanCreateSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        plan = ser.save()
        
        log_work_plan_created(plan.object.name, plan.title, request.user.full_name, request.user.role)
        
        return Response(WorkPlanOutSerializer(plan).data, status=status.HTTP_201_CREATED)

class WorkPlanDetailView(APIView):
    def get(self, request, id: int):
        try:
            wp = WorkPlan.objects.select_related("object","created_by").prefetch_related("items__schedule_item", "items__sub_areas").get(id=id)
        except WorkPlan.DoesNotExist:
            return Response({"detail":"Not found"}, status=404)
        if wp.object_id not in _visible_object_ids_for_user(request.user):
            return Response({"detail":"Forbidden"}, status=403)
        return Response(WorkPlanDetailOutSerializer(wp).data, status=200)

class WorkPlansListView(APIView):
    def get(self, request):
        visible_object_ids = _visible_object_ids_for_user(request.user)
        qs = WorkPlan.objects.filter(object_id__in=visible_object_ids).select_related("object", "created_by").prefetch_related("items__schedule_item", "items__sub_areas").order_by("-created_at")
        
        object_id = request.query_params.get("object_id")
        if object_id:
            qs = qs.filter(object_id=object_id)
        
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
        
        if si.status == "done":
            log_work_item_completed(si.object.name, si.work_item.name, request.user.full_name, request.user.role)
        
        return Response({"status": si.status}, status=200)


class WorkItemDetailView(APIView):
    def get(self, request, id: int):
        try:
            work_item = WorkItem.objects.select_related(
                "plan__object", "schedule_item"
            ).prefetch_related(
                "sub_areas", 
                "deliveries__materials",
                "deliveries__created_by"
            ).get(id=id)
        except WorkItem.DoesNotExist:
            return Response({"detail": "Позиция перечня работ не найдена"}, status=404)
        
        visible_object_ids = _visible_object_ids_for_user(request.user)
        if work_item.plan.object_id not in visible_object_ids:
            return Response({"detail": "Forbidden"}, status=403)
        
        return Response(WorkItemDetailSerializer(work_item).data, status=200)


class WorkPlanChangeRequestView(APIView):
    
    def post(self, request):
        ser = WorkPlanChangeRequestSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        
        work_plan = ser.context["work_plan"]
        new_items = ser.validated_data["items"]
        comment = ser.validated_data.get("comment", "")
        
        current_items = list(WorkItem.objects.filter(plan=work_plan).values(
            'id', 'name', 'quantity', 'unit', 'start_date', 'end_date', 'document_url'
        ))
        
        changes_analysis = self._analyze_changes(current_items, new_items)
        
        if request.user.role in [Roles.SSK, Roles.ADMIN]:
            return self._apply_changes_directly(work_plan, changes_analysis, request)
        
        change_request = WorkItemChangeRequest.objects.create(
            work_plan=work_plan,
            requested_by=request.user,
            comment=comment,
            old_items_data=current_items,
            new_items_data=new_items,
            changes_data=changes_analysis
        )
        
        self._send_notification_to_ssk(work_plan, change_request, request)
        
        return Response({
            "change_request_id": change_request.id,
            "status": "pending",
            "message": "Запрос на изменение отправлен ССК на рассмотрение",
            "changes_summary": changes_analysis
        }, status=201)
    
    def _analyze_changes(self, current_items, new_items):
        current_dict = {item['id']: item for item in current_items}
        new_dict = {item.get('id'): item for item in new_items if item.get('id')}
        
        analysis = {
            'added': [],
            'deleted': [],
            'modified': [],
            'unchanged': []
        }
        
        for item in new_items:
            if not item.get('id') or item['id'] not in current_dict:
                analysis['added'].append(item)
        
        for current_id, current_item in current_dict.items():
            if current_id not in new_dict:
                analysis['deleted'].append(current_item)
            else:
                new_item = new_dict[current_id]
                if self._items_different(current_item, new_item):
                    analysis['modified'].append({
                        'old': current_item,
                        'new': new_item
                    })
                else:
                    analysis['unchanged'].append(current_item)
        
        return analysis
    
    def _items_different(self, old_item, new_item):
        fields_to_compare = ['name', 'quantity', 'unit', 'start_date', 'end_date', 'document_url']
        
        for field in fields_to_compare:
            old_value = old_item.get(field)
            new_value = new_item.get(field)
            
            if field == 'quantity':
                old_value = float(old_value) if old_value is not None else None
                new_value = float(new_value) if new_value is not None else None
            
            if old_value != new_value:
                return True
        
        return False
    
    def _apply_changes_directly(self, work_plan, changes_analysis, request):
        with transaction.atomic():
            for deleted_item in changes_analysis['deleted']:
                try:
                    work_item = WorkItem.objects.get(id=deleted_item['id'], plan=work_plan)
                    work_item.delete()
                except WorkItem.DoesNotExist:
                    continue
            
            for added_item in changes_analysis['added']:
                work_item = WorkItem.objects.create(
                    plan=work_plan,
                    name=added_item['name'],
                    quantity=added_item.get('quantity'),
                    unit=added_item.get('unit', ''),
                    start_date=added_item['start_date'],
                    end_date=added_item['end_date'],
                    document_url=added_item.get('document_url', '')
                )
                ScheduleItem.objects.create(
                    object=work_plan.object,
                    work_item=work_item,
                    planned_start=work_item.start_date,
                    planned_end=work_item.end_date,
                    status="planned"
                )
                
                # Создаем подполигоны для новой позиции
                self._create_sub_areas_for_work_item(work_plan.object, work_item, added_item.get('sub_areas', []))
            
            for modified_item in changes_analysis['modified']:
                try:
                    work_item = WorkItem.objects.get(id=modified_item['old']['id'], plan=work_plan)
                    new_data = modified_item['new']
                    
                    work_item.name = new_data['name']
                    work_item.quantity = new_data.get('quantity')
                    work_item.unit = new_data.get('unit', '')
                    work_item.start_date = new_data['start_date']
                    work_item.end_date = new_data['end_date']
                    work_item.document_url = new_data.get('document_url', '')
                    work_item.save()
                    
                    if hasattr(work_item, 'schedule_item'):
                        schedule_item = work_item.schedule_item
                        schedule_item.planned_start = work_item.start_date
                        schedule_item.planned_end = work_item.end_date
                        schedule_item.save()
                except WorkItem.DoesNotExist:
                    continue
            
            self._send_notification_after_change(work_plan, request)
        
        return Response({
            "status": "applied",
            "message": "Изменения применены успешно",
            "changes_summary": changes_analysis
        }, status=200)
    
    def _send_notification_to_ssk(self, work_plan, change_request, request):
        if work_plan.object.ssk_id and work_plan.object.ssk:
            from api.api.v1.views.utils import send_notification
            try:
                send_notification(
                    work_plan.object.ssk_id,
                    work_plan.object.ssk.email,
                    "Запрос на изменение графика работ",
                    f"Прораб {request.user.full_name} запросил изменения в графике работ для объекта '{work_plan.object.name}'. Требуется ваше рассмотрение.",
                    request.user.full_name, request.user.role
                )
            except Exception:
                pass
    
    def _send_notification_after_change(self, work_plan, request):
        from api.api.v1.views.utils import send_notification
        
        if work_plan.object.foreman_id and work_plan.object.foreman:
            try:
                send_notification(
                    work_plan.object.foreman_id,
                    work_plan.object.foreman.email,
                    "График работ изменен",
                    f"График работ для объекта '{work_plan.object.name}' был изменен {request.user.full_name}.",
                    request.user.full_name, request.user.role
                )
            except Exception:
                pass
        
        if work_plan.object.iko_id and work_plan.object.iko:
            try:
                send_notification(
                    work_plan.object.iko_id,
                    work_plan.object.iko.email,
                    "График работ изменен",
                    f"График работ для объекта '{work_plan.object.name}' был изменен {request.user.full_name}.",
                    request.user.full_name, request.user.role
                )
            except Exception:
                pass

    def _create_sub_areas_for_work_item(self, construction_object, work_item, sub_areas_data):
        """Создает подполигоны для позиции перечня работ"""
        from api.models.area import Area, SubArea
        
        if not sub_areas_data:
            return
        
        # Получаем первую область объекта (или создаем если нет)
        area = construction_object.areas.first()
        if not area:
            area = Area.objects.create(
                name=f"Основная область {construction_object.name}",
                geometry={"type": "Polygon", "coordinates": []},
                object=construction_object
            )
        
        # Создаем подполигоны
        for sub_area_data in sub_areas_data:
            SubArea.objects.create(
                name=sub_area_data["name"],
                geometry=sub_area_data["geometry"],
                color=sub_area_data.get("color", "#FF0000"),
                area=area,
                work_item=work_item,
            )


class WorkPlanChangeDecisionView(APIView):
    permission_classes = [RoleRequired.as_permitted(Roles.SSK, Roles.ADMIN)]
    
    def post(self, request, change_request_id: int):
        try:
            change_request = WorkItemChangeRequest.objects.select_related('work_plan__object').get(id=change_request_id)
        except WorkItemChangeRequest.DoesNotExist:
            return Response({"detail": "Запрос на изменение не найден"}, status=404)
        
        if request.user.role != Roles.ADMIN and change_request.work_plan.object.ssk_id != request.user.id:
            return Response({"detail": "Forbidden"}, status=403)
        
        ser = WorkPlanChangeDecisionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        
        decision = ser.validated_data["decision"]
        comment = ser.validated_data.get("comment", "")
        edited_items = ser.validated_data.get("edited_items", [])
        
        with transaction.atomic():
            change_request.decided_by = request.user
            change_request.comment = comment
            
            if decision == "approve":
                self._apply_changes_to_work_plan(change_request.work_plan, change_request.changes_data)
                change_request.status = "approved"
            elif decision == "reject":
                change_request.status = "rejected"
            elif decision == "edit":
                edited_analysis = self._analyze_changes(change_request.old_items_data, edited_items)
                self._apply_changes_to_work_plan(change_request.work_plan, edited_analysis)
                change_request.status = "edited"
                change_request.new_items_data = edited_items
            
            change_request.save()
            
            self._send_notification_after_decision(change_request, request)
        
        return Response({
            "status": change_request.status,
            "message": f"Решение принято: {decision}"
        }, status=200)
    
    def _apply_changes_to_work_plan(self, work_plan, changes_analysis):
        for deleted_item in changes_analysis['deleted']:
            try:
                work_item = WorkItem.objects.get(id=deleted_item['id'], plan=work_plan)
                work_item.delete()
            except WorkItem.DoesNotExist:
                continue
        
        for added_item in changes_analysis['added']:
            work_item = WorkItem.objects.create(
                plan=work_plan,
                name=added_item['name'],
                quantity=added_item.get('quantity'),
                unit=added_item.get('unit', ''),
                start_date=added_item['start_date'],
                end_date=added_item['end_date'],
                document_url=added_item.get('document_url', '')
            )
            ScheduleItem.objects.create(
                object=work_plan.object,
                work_item=work_item,
                planned_start=work_item.start_date,
                planned_end=work_item.end_date,
                status="planned"
            )
            
            # Создаем подполигоны для новой позиции
            self._create_sub_areas_for_work_item(work_plan.object, work_item, added_item.get('sub_areas', []))
        
        for modified_item in changes_analysis['modified']:
            try:
                work_item = WorkItem.objects.get(id=modified_item['old']['id'], plan=work_plan)
                new_data = modified_item['new']
                
                work_item.name = new_data['name']
                work_item.quantity = new_data.get('quantity')
                work_item.unit = new_data.get('unit', '')
                work_item.start_date = new_data['start_date']
                work_item.end_date = new_data['end_date']
                work_item.document_url = new_data.get('document_url', '')
                work_item.save()
                
                if hasattr(work_item, 'schedule_item'):
                    schedule_item = work_item.schedule_item
                    schedule_item.planned_start = work_item.start_date
                    schedule_item.planned_end = work_item.end_date
                    schedule_item.save()
            except WorkItem.DoesNotExist:
                continue
    
    def _create_sub_areas_for_work_item(self, construction_object, work_item, sub_areas_data):
        """Создает подполигоны для позиции перечня работ"""
        from api.models.area import Area, SubArea
        
        if not sub_areas_data:
            return
        
        # Получаем первую область объекта (или создаем если нет)
        area = construction_object.areas.first()
        if not area:
            area = Area.objects.create(
                name=f"Основная область {construction_object.name}",
                geometry={"type": "Polygon", "coordinates": []},
                object=construction_object
            )
        
        # Создаем подполигоны
        for sub_area_data in sub_areas_data:
            SubArea.objects.create(
                name=sub_area_data["name"],
                geometry=sub_area_data["geometry"],
                color=sub_area_data.get("color", "#FF0000"),
                area=area,
                work_item=work_item,
            )
    
    def _send_notification_after_decision(self, change_request, request):
        from api.api.v1.views.utils import send_notification
        
        if change_request.requested_by:
            try:
                send_notification(
                    change_request.requested_by.id,
                    change_request.requested_by.email,
                    "Решение по изменению графика работ",
                    f"Ваш запрос на изменение графика работ для объекта '{change_request.work_plan.object.name}' {change_request.get_status_display().lower()}.",
                    request.user.full_name, request.user.role
                )
            except Exception:
                pass
        
        if change_request.work_plan.object.iko_id and change_request.work_plan.object.iko:
            try:
                send_notification(
                    change_request.work_plan.object.iko_id,
                    change_request.work_plan.object.iko.email,
                    "График работ изменен",
                    f"График работ для объекта '{change_request.work_plan.object.name}' был изменен.",
                    request.user.full_name, request.user.role
                )
            except Exception:
                pass


class WorkPlanChangeRequestsListView(APIView):
    
    def get(self, request):
        visible_object_ids = _visible_object_ids_for_user(request.user)
        
        qs = WorkItemChangeRequest.objects.filter(
            work_plan__object_id__in=visible_object_ids
        ).select_related(
            'work_plan__object', 'requested_by', 'decided_by'
        ).order_by('-created_at')
        
        status = request.query_params.get('status')
        if status:
            qs = qs.filter(status=status)
        
        object_id = request.query_params.get('object_id')
        if object_id:
            qs = qs.filter(work_plan__object_id=object_id)
        
        page, total = _paginated(qs, request)
        return Response({
            "items": WorkItemChangeRequestOutSerializer(page, many=True).data,
            "total": total
        }, status=200)
