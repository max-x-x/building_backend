from rest_framework.views import APIView
from rest_framework.response import Response
from api.models.user import Roles
from api.models.delivery import Delivery, Invoice, LabOrder
from api.models.object import ConstructionObject
from api.api.v1.views.objects import _visible_object_ids_for_user, _paginated
from api.serializers.deliveries import (DeliveryCreateSerializer, DeliveryOutSerializer, DeliveryReceiveSerializer,
                                        InvoiceCreateSerializer, ParseTTNSerializer, DeliveryStatusSerializer,
                                        LabOrderCreateSerializer)


class DeliveriesCreateView(APIView):
    def post(self, request):
        if request.user.role not in (Roles.SSK, Roles.ADMIN):
            return Response({"detail":"Forbidden"}, status=403)
        ser = DeliveryCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            obj = ConstructionObject.objects.get(id=ser.validated_data["object_id"])
        except ConstructionObject.DoesNotExist:
            return Response({"detail":"Object not found"}, status=404)
        if request.user.role != Roles.ADMIN and obj.ssk_id != request.user.id:
            return Response({"detail":"Forbidden"}, status=403)
        d = Delivery.objects.create(
            object=obj,
            planned_date=ser.validated_data.get("planned_date"),
            notes=ser.validated_data.get("notes",""),
            created_by=request.user
        )
        return Response(DeliveryOutSerializer(d).data, status=201)

class DeliveryReceiveView(APIView):
    def post(self, request, id: int):
        ser = DeliveryReceiveSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            d = Delivery.objects.select_related("object").get(id=id)
        except Delivery.DoesNotExist:
            return Response({"detail":"Not found"}, status=404)
        if request.user.role not in (Roles.FOREMAN, Roles.ADMIN):
            return Response({"detail":"Forbidden"}, status=403)
        if request.user.role != Roles.ADMIN and d.object.foreman_id != request.user.id:
            return Response({"detail":"Forbidden"}, status=403)
        d.status = "received"
        d.notes = ser.validated_data.get("notes","")
        d.save(update_fields=["status","notes","modified_at"])
        return Response(DeliveryOutSerializer(d).data, status=201)

class DeliveriesListView(APIView):
    def get(self, request):
        visible = _visible_object_ids_for_user(request.user)
        qs = Delivery.objects.filter(object_id__in=visible).order_by("-created_at")
        object_id = request.query_params.get("object_id")
        if object_id:
            qs = qs.filter(object_id=object_id)
        page, total = _paginated(qs, request)
        return Response({"items": DeliveryOutSerializer(page, many=True).data, "total": total}, status=200)

class InvoicesCreateView(APIView):
    def post(self, request):
        if request.user.role not in (Roles.FOREMAN, Roles.SSK, Roles.ADMIN):
            return Response({"detail":"Forbidden"}, status=403)
        ser = InvoiceCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            obj = ConstructionObject.objects.get(id=ser.validated_data["object_id"])
        except ConstructionObject.DoesNotExist:
            return Response({"detail":"Object not found"}, status=404)

        d = None
        if ser.validated_data.get("delivery_id"):
            d = Delivery.objects.filter(id=ser.validated_data["delivery_id"], object=obj).first()
        if not d and ser.validated_data.get("delivery_uuid"):
            d = Delivery.objects.filter(uuid_delivery=ser.validated_data["delivery_uuid"], object=obj).first()
        if not d:
            return Response({"detail":"Delivery not found"}, status=404)

        inv = Invoice.objects.create(
            object=obj, delivery=d,
            pdf_url=ser.validated_data["pdf_url"],
            data=ser.validated_data.get("data", {})
        )
        return Response({"id": inv.id, "uuid_invoice": str(inv.uuid_invoice)}, status=201)

class InvoiceParseTTNView(APIView):
    def post(self, request, id: int):
        ser = ParseTTNSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        # мок распознавания
        data = {
            "supplier": "ООО Поставщик",
            "number": "TTN-12345",
            "date": "2025-09-01",
            "items": [{"name":"Щебень", "qty": 20, "unit":"т", "price": 1500}],
            "totals": {"sum": 30000}
        }
        return Response({"data": data}, status=200)

class DeliverySetStatusView(APIView):
    def post(self, request, id: int):
        if request.user.role not in (Roles.SSK, Roles.ADMIN):
            return Response({"detail":"Forbidden"}, status=403)
        ser = DeliveryStatusSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            d = Delivery.objects.select_related("object").get(id=id)
        except Delivery.DoesNotExist:
            return Response({"detail":"Not found"}, status=404)
        if request.user.role != Roles.ADMIN and d.object.ssk_id != request.user.id:
            return Response({"detail":"Forbidden"}, status=403)
        d.status = ser.validated_data["status"]
        d.save(update_fields=["status","modified_at"])
        return Response(DeliveryOutSerializer(d).data, status=200)

class LabOrdersCreateView(APIView):
    def post(self, request):
        if request.user.role not in (Roles.SSK, Roles.ADMIN):
            return Response({"detail":"Forbidden"}, status=403)
        ser = LabOrderCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = None
        if ser.validated_data.get("delivery_id"):
            d = Delivery.objects.filter(id=ser.validated_data["delivery_id"]).first()
        if not d and ser.validated_data.get("delivery_uuid"):
            d = Delivery.objects.filter(uuid_delivery=ser.validated_data["delivery_uuid"]).first()
        if not d:
            return Response({"detail":"Delivery not found"}, status=404)
        if request.user.role != Roles.ADMIN and d.object.ssk_id != request.user.id:
            return Response({"detail":"Forbidden"}, status=403)
        lo = LabOrder.objects.create(delivery=d, items=ser.validated_data["items"])
        d.status = "sent_to_lab"
        d.save(update_fields=["status"])
        return Response({"order_id": lo.id, "uuid_lab_order": str(lo.uuid_lab_order), "status": lo.status}, status=201)