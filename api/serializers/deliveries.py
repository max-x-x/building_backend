from rest_framework import serializers

from api.models.delivery import Delivery, Invoice, Material


class DeliveryCreateSerializer(serializers.Serializer):
    object_id = serializers.IntegerField()
    planned_date = serializers.DateField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True)

class MaterialSerializer(serializers.ModelSerializer):
    """Сериализатор для материала."""
    class Meta:
        model = Material
        fields = ("id", "uuid_material", "material_name", "material_quantity", "material_size", 
                "material_volume", "material_netto", "is_confirmed", "created_at", "modified_at")

class InvoiceSerializer(serializers.ModelSerializer):
    """Сериализатор для накладной с материалами."""
    materials = MaterialSerializer(many=True, read_only=True)
    
    class Meta:
        model = Invoice
        fields = ("id", "uuid_invoice", "pdf_url", "folder_url", "data", "materials", "created_at", "modified_at")

class DeliveryOutSerializer(serializers.ModelSerializer):
    """Сериализатор для поставки с накладными и материалами."""
    invoices = InvoiceSerializer(many=True, read_only=True)
    
    class Meta:
        model = Delivery
        fields = ("id", "uuid_delivery", "object", "planned_date", "notes", "status", 
                "created_by", "invoices", "created_at", "modified_at")

class DeliveryReceiveSerializer(serializers.Serializer):
    object_id = serializers.IntegerField()
    notes = serializers.CharField(required=False, allow_blank=True)

class InvoiceCreateSerializer(serializers.Serializer):
    object_id = serializers.IntegerField()
    delivery_id = serializers.IntegerField(required=False)  # будем принимать по int id из БД
    delivery_uuid = serializers.UUIDField(required=False)   # альтернативно по uuid_delivery
    pdf_url = serializers.URLField()
    folder_url = serializers.URLField(required=False, allow_blank=True)
    data = serializers.JSONField(required=False)

class InvoiceDataSerializer(serializers.Serializer):
    """Сериализатор для данных от внешнего сервиса CV."""
    delivery_id = serializers.IntegerField()
    folder_url = serializers.URLField()
    materials_data = serializers.ListField(
        child=serializers.DictField(),
        help_text="Список материалов из распознанных данных"
    )

class MaterialUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления материала."""
    class Meta:
        model = Material
        fields = ("material_name", "material_quantity", "material_size", 
                 "material_volume", "material_netto", "is_confirmed")

class DeliveryConfirmSerializer(serializers.Serializer):
    """Сериализатор для подтверждения поставки."""
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
    items = serializers.ListField(child=serializers.DictField())  # [{invoice_item_id,sample_code}]
    lab_id = serializers.CharField(required=False, allow_blank=True)