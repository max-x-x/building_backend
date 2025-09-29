from rest_framework import serializers

from api.models.ticket import Ticket


class TicketCreateSerializer(serializers.Serializer):
    object_id = serializers.IntegerField(required=False)
    text = serializers.CharField()

class TicketOutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = "__all__"