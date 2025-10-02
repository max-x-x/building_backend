from rest_framework import serializers

from api.models.delivery import Delivery, Invoice, Material


class DeliveryCreateSerializer(serializers.Serializer):
    object_id = serializers.IntegerField()
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
        
        delivery = Delivery.objects.create(**self.validated_data, **kwargs)
        
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

class DeliveryOutSerializer(serializers.ModelSerializer):
    invoices = InvoiceSerializer(many=True, read_only=True)
    materials = MaterialSerializer(many=True, read_only=True)
    
    class Meta:
        model = Delivery
        fields = ("id", "uuid_delivery", "object", "planned_date", "notes", "status", 
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