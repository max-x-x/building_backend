from rest_framework import serializers
from api.models.documents import DocumentFile, ExecDocument

class DocumentOutSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentFile
        fields = ("id","uuid_document","object","folder","name","url","size_bytes","content_type","created_at")

class ExecDocCreateSerializer(serializers.Serializer):
    object_id = serializers.IntegerField()
    kind = serializers.ChoiceField(choices=[k for k,_ in ExecDocument.KIND])
    pdf_url = serializers.URLField()

class ExecDocOutSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExecDocument
        fields = ("id","uuid_execdoc","object","kind","pdf_url","created_by","created_at")
