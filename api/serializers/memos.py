from rest_framework import serializers

from api.models.memo import Memo


class MemoCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=300)
    pdf_url = serializers.URLField()

class MemoOutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Memo
        fields = ("id","uuid_memo","title","pdf_url","created_at")
