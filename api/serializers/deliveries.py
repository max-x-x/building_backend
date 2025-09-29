from rest_framework import serializers

from api.models.delivery import Delivery


class DeliveryCreateSerializer(serializers.Serializer):
    object_id = serializers.IntegerField()
    planned_date = serializers.DateField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True)

class DeliveryOutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Delivery
        fields = "__all__"

class DeliveryReceiveSerializer(serializers.Serializer):
    object_id = serializers.IntegerField()
    notes = serializers.CharField(required=False, allow_blank=True)

class InvoiceCreateSerializer(serializers.Serializer):
    object_id = serializers.IntegerField()
    delivery_id = serializers.IntegerField(required=False)  # будем принимать по int id из БД
    delivery_uuid = serializers.UUIDField(required=False)   # альтернативно по uuid_delivery
    pdf_url = serializers.URLField()
    data = serializers.JSONField(required=False)

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