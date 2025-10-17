from rest_framework import serializers

from api.models.delivery import Delivery, Invoice, Material
from api.models.work_plan import WorkItem


class DeliveryCreateSerializer(serializers.Serializer):
    object_id = serializers.IntegerField()
    work_item_id = serializers.IntegerField(required=False, allow_null=True, help_text="ID позиции перечня работ")
    planned_date = serializers.DateField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True)
    invoice_photos = serializers.ListField(
        child=serializers.CharField(), 
        required=False, 
        help_text="Список фото накладных в формате base64"
    )
    
    def save(self, **kwargs):
        from api.models.delivery import Delivery
        from api.utils.file_storage import upload_invoice_photos_base64
        
        invoice_photos = self.validated_data.pop("invoice_photos", [])
        work_item_id = self.validated_data.pop("work_item_id", None)
        
        # Получаем work_item если указан ID
        work_item = None
        if work_item_id:
            try:
                work_item = WorkItem.objects.select_related('plan__object').get(id=work_item_id)
                # Проверяем, что позиция принадлежит тому же объекту
                object_id = self.validated_data.get('object_id')
                if work_item.plan.object_id != object_id:
                    raise serializers.ValidationError({"work_item_id": "Позиция перечня работ не принадлежит указанному объекту"})
            except WorkItem.DoesNotExist:
                raise serializers.ValidationError({"work_item_id": "Позиция перечня работ не найдена"})
        
        delivery = Delivery.objects.create(**self.validated_data, work_item=work_item, **kwargs)
        
        if invoice_photos:
            request = self.context.get("request")
            user_name = request.user.full_name if request and request.user else "Система"
            user_role = request.user.role if request and request.user else "system"
            
            urls = upload_invoice_photos_base64(invoice_photos, delivery.object_id, delivery.id, user_name, user_role)
            
            if urls:
                delivery.invoice_photos_folder_url = urls
                delivery.save(update_fields=["invoice_photos_folder_url"])
        
        return delivery

class MaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Material
        fields = ("id", "uuid_material", "material_name", "material_quantity", "material_size", 
                "material_volume", "material_netto", "is_confirmed", "created_at", "modified_at")

class InvoiceSerializer(serializers.ModelSerializer):
    materials = MaterialSerializer(many=True, read_only=True)
    
    class Meta:
        model = Invoice
        fields = ("id", "uuid_invoice", "pdf_url", "folder_url", "data", "materials", "created_at", "modified_at")

class WorkItemBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkItem
        fields = ("id", "uuid_wi", "name", "quantity", "unit", "start_date", "end_date")

class DeliveryOutSerializer(serializers.ModelSerializer):
    invoices = InvoiceSerializer(many=True, read_only=True)
    materials = MaterialSerializer(many=True, read_only=True)
    work_item = WorkItemBriefSerializer(read_only=True)
    
    class Meta:
        model = Delivery
        fields = ("id", "uuid_delivery", "object", "work_item", "planned_date", "notes", "status", 
                "created_by", "invoices", "materials", "invoice_photos_folder_url", "created_at", "modified_at")

class DeliveryReceiveSerializer(serializers.Serializer):
    object_id = serializers.IntegerField()
    notes = serializers.CharField(required=False, allow_blank=True)
    invoice_photos = serializers.ListField(
        child=serializers.CharField(), 
        required=False, 
        help_text="Список фото накладных в формате base64"
    )

class InvoiceCreateSerializer(serializers.Serializer):
    object_id = serializers.IntegerField()
    delivery_id = serializers.IntegerField(required=False)
    delivery_uuid = serializers.UUIDField(required=False)
    pdf_url = serializers.URLField()
    folder_url = serializers.URLField(required=False, allow_blank=True)
    data = serializers.JSONField(required=False)

class InvoiceDataSerializer(serializers.Serializer):
    delivery_id = serializers.IntegerField()
    folder_url = serializers.URLField()
    materials_data = serializers.ListField(
        child=serializers.DictField(),
        help_text="Список материалов из распознанных данных"
    )

class MaterialUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Material
        fields = ("material_name", "material_quantity", "material_size", 
                 "material_volume", "material_netto", "is_confirmed")

class DeliveryConfirmSerializer(serializers.Serializer):
    materials = MaterialUpdateSerializer(many=True)
    status = serializers.ChoiceField(choices=["received", "accepted", "sent_to_lab"])

class ParseTTNSerializer(serializers.Serializer):
    image_urls = serializers.ListField(child=serializers.URLField())

class DeliveryStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["accepted","rejected","sent_to_lab","awaiting_lab"])
    comment = serializers.CharField(required=False, allow_blank=True)

class LabOrderCreateSerializer(serializers.Serializer):
    delivery_id = serializers.IntegerField(required=False)
    delivery_uuid = serializers.UUIDField(required=False)
    items = serializers.ListField(child=serializers.DictField())
    lab_id = serializers.CharField(required=False, allow_blank=True)