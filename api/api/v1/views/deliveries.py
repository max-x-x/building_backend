from rest_framework.views import APIView
from rest_framework.response import Response
from api.models.user import Roles
from api.models.delivery import Delivery, Invoice, LabOrder, Material
from api.models.object import ConstructionObject
from api.api.v1.views.objects import _visible_object_ids_for_user, _paginated
from api.serializers.deliveries import (DeliveryCreateSerializer, DeliveryOutSerializer, DeliveryReceiveSerializer,
                                        InvoiceCreateSerializer, ParseTTNSerializer, DeliveryStatusSerializer,
                                        LabOrderCreateSerializer, InvoiceDataSerializer, DeliveryConfirmSerializer)
from api.utils.logging import log_delivery_created, log_delivery_received, log_delivery_accepted, log_delivery_sent_to_lab


class DeliveriesCreateView(APIView):
    def post(self, request):
        if request.user.role not in (Roles.SSK, Roles.ADMIN):
            return Response({"detail":"Forbidden"}, status=403)
        ser = DeliveryCreateSerializer(data=request.data, context={'request': request})
        ser.is_valid(raise_exception=True)
        try:
            obj = ConstructionObject.objects.get(id=ser.validated_data["object_id"])
        except ConstructionObject.DoesNotExist:
            return Response({"detail":"Object not found"}, status=404)
        if request.user.role != Roles.ADMIN and obj.ssk_id != request.user.id:
            return Response({"detail":"Forbidden"}, status=403)
        d = ser.save(object=obj, created_by=request.user)
        
        log_delivery_created(obj.name, d.id, request.user.full_name, request.user.role)
        
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
        
        invoice_photos = ser.validated_data.get("invoice_photos", [])
        if invoice_photos:
            from api.utils.file_storage import upload_invoice_photos_base64
            
            urls = upload_invoice_photos_base64(invoice_photos, d.object_id, d.id, request.user.full_name, request.user.role)
            
            if urls:
                d.invoice_photos_folder_url = urls
        
        d.status = "received"
        d.notes = ser.validated_data.get("notes","")
        d.save(update_fields=["status","notes","invoice_photos_folder_url","modified_at"])
        return Response(DeliveryOutSerializer(d).data, status=201)

class DeliveriesListView(APIView):
    def get(self, request):
        visible = _visible_object_ids_for_user(request.user)
        qs = Delivery.objects.filter(object_id__in=visible).prefetch_related('invoices', 'materials').order_by("-created_at")
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


class InvoiceDataReceiveView(APIView):
    def post(self, request):
        ser = InvoiceDataSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        
        try:
            delivery = Delivery.objects.get(id=ser.validated_data["delivery_id"])
        except Delivery.DoesNotExist:
            return Response({"detail": "Delivery not found"}, status=404)
        
        folder_url = ser.validated_data["folder_url"]
        materials_data = ser.validated_data["materials_data"]
        
        invoice = Invoice.objects.create(
            object=delivery.object,
            delivery=delivery,
            pdf_url="",
            folder_url=folder_url,
            data={"materials_count": len(materials_data)}
        )

        created_materials = []
        for material_data in materials_data:
            material = Material.objects.create(
                delivery=delivery,
                invoice=invoice,
                material_name=material_data.get("Наименование материала", ""),
                material_quantity=material_data.get("Количество материала", ""),
                material_size=material_data.get("Размер", ""),
                material_volume=material_data.get("Объем", ""),
                material_netto=material_data.get("Нетто", "")
            )
            created_materials.append(material)
        
        return Response({
            "invoice_id": invoice.id,
            "materials_count": len(created_materials),
            "status": "success"
        }, status=201)


class DeliveryConfirmView(APIView):

    def post(self, request, id: int):
        try:
            delivery = Delivery.objects.prefetch_related('invoices', 'materials').get(id=id)
        except Delivery.DoesNotExist:
            return Response({"detail": "Delivery not found"}, status=404)
        
        ser = DeliveryConfirmSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        requested_status = ser.validated_data["status"]
        
        if request.user.role == Roles.FOREMAN:
            if delivery.object.foreman_id != request.user.id:
                return Response({"detail": "Forbidden"}, status=403)
            if requested_status != "received":
                return Response({"detail": "Foreman can only set status to 'received'"}, status=400)
            expected_status = "received"
        elif request.user.role == Roles.SSK:
            if delivery.object.ssk_id != request.user.id:
                return Response({"detail": "Forbidden"}, status=403)
            if requested_status not in ["accepted", "sent_to_lab"]:
                return Response({"detail": "SSK can only accept or send to lab"}, status=400)
            expected_status = requested_status
        elif request.user.role == Roles.ADMIN:
            expected_status = requested_status
        else:
            return Response({"detail": "Forbidden"}, status=403)

        materials_data = ser.validated_data["materials"]
        for material_data in materials_data:
            material_id = material_data.get("id")
            if material_id:
                try:
                    material = Material.objects.get(id=material_id, delivery=delivery)
                    for field, value in material_data.items():
                        if field != "id" and hasattr(material, field):
                            setattr(material, field, value)
                    material.save()
                except Material.DoesNotExist:
                    continue

        delivery.status = expected_status
        delivery.save(update_fields=["status"])

        if expected_status == "received":
            log_delivery_received(delivery.object.name, delivery.id, request.user.full_name, request.user.role)
        elif expected_status == "accepted":
            log_delivery_accepted(delivery.object.name, delivery.id, request.user.full_name, request.user.role)
        elif expected_status == "sent_to_lab":
            log_delivery_sent_to_lab(delivery.object.name, delivery.id, request.user.full_name, request.user.role)

        from api.api.v1.views.utils import send_notification
        try:
            if expected_status == "received":
                if delivery.object.ssk_id and delivery.object.ssk:
                    send_notification(
                        delivery.object.ssk_id,
                        delivery.object.ssk.email,
                        "Поставка принята прорабом",
                        f"Поставка #{delivery.id} для объекта '{delivery.object.name}' принята прорабом. Требуется ваше подтверждение.",
                        request.user.full_name, request.user.role
                    )
            elif expected_status == "accepted":
                if delivery.object.foreman_id and delivery.object.foreman:
                    send_notification(
                        delivery.object.foreman_id,
                        delivery.object.foreman.email,
                        "Поставка подтверждена ССК",
                        f"Поставка #{delivery.id} для объекта '{delivery.object.name}' подтверждена ССК.",
                        request.user.full_name, request.user.role
                    )
            elif expected_status == "sent_to_lab":
                if delivery.object.foreman_id and delivery.object.foreman:
                    send_notification(
                        delivery.object.foreman_id,
                        delivery.object.foreman.email,
                        "Поставка отправлена в лабораторию",
                        f"Поставка #{delivery.id} для объекта '{delivery.object.name}' отправлена в лабораторию.",
                        request.user.full_name, request.user.role
                    )
        except Exception:
            pass
        
        return Response(DeliveryOutSerializer(delivery).data, status=200)


class DeliveryDetailView(APIView):

    def get(self, request, id: int):
        try:
            delivery = Delivery.objects.select_related("object", "created_by").prefetch_related("invoices__materials").get(id=id)
        except Delivery.DoesNotExist:
            return Response({"detail": "Delivery not found"}, status=404)

        visible_object_ids = _visible_object_ids_for_user(request.user)
        if delivery.object_id not in visible_object_ids:
            return Response({"detail": "Forbidden"}, status=403)
        
        return Response(DeliveryOutSerializer(delivery).data, status=200)