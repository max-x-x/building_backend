from rest_framework import serializers
from api.models.prescription import Prescription, PrescriptionFix
from api.serializers.objects import ObjectShortSerializer


class PrescriptionCreateSerializer(serializers.ModelSerializer):
    violation_photos_urls = serializers.ListField(
        child=serializers.URLField(), 
        required=False, 
        help_text="Список ссылок на фото нарушения"
    )
    
    class Meta:
        model = Prescription
        fields = ("object", "title", "description", "requires_stop", "requires_personal_recheck", "attachments", "violation_photos_urls")
    
    def save(self, **kwargs):
        violation_photos_urls = self.validated_data.pop("violation_photos_urls", [])
        
        prescription = super().save(**kwargs)
        
        if violation_photos_urls:
            prescription.violation_photos_folder_url = violation_photos_urls
            prescription.save(update_fields=["violation_photos_folder_url"])
        
        return prescription

class PrescriptionFixSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrescriptionFix
        fields = ("id", "uuid_fix", "author", "comment", "attachments", "fix_photos_folder_url", "created_at")

class PrescriptionOutSerializer(serializers.ModelSerializer):
    fixes = PrescriptionFixSerializer(many=True, read_only=True)
    
    class Meta:
        model = Prescription
        fields = "__all__"

class PrescriptionFixCreateSerializer(serializers.ModelSerializer):
    fix_photos_urls = serializers.ListField(
        child=serializers.URLField(), 
        required=False, 
        help_text="Список ссылок на фото исправления нарушения"
    )
    
    class Meta:
        model = PrescriptionFix
        fields = ("comment", "attachments", "fix_photos_urls")
    
    def save(self, **kwargs):
        fix_photos_urls = self.validated_data.pop("fix_photos_urls", [])
        
        prescription_fix = super().save(**kwargs)
        
        if fix_photos_urls:
            prescription_fix.fix_photos_folder_url = fix_photos_urls
            prescription_fix.save(update_fields=["fix_photos_folder_url"])
        
        return prescription_fix

class PrescriptionListSerializer(serializers.ModelSerializer):
    object = ObjectShortSerializer(read_only=True)
    fixes = PrescriptionFixSerializer(many=True, read_only=True)

    class Meta:
        model = Prescription
        fields = (
            "id", "uuid_prescription",
            "object", "author", "title",
            "requires_stop", "requires_personal_recheck", "description",
            "status", "violation_photos_folder_url", "fixes", "created_at", "closed_at",
        )