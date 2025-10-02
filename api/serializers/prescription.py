from rest_framework import serializers
from api.models.prescription import Prescription, PrescriptionFix
from api.serializers.objects import ObjectShortSerializer


class PrescriptionCreateSerializer(serializers.ModelSerializer):
    violation_photos = serializers.ListField(
        child=serializers.CharField(), 
        required=False, 
        help_text="Список фото нарушения в формате base64"
    )
    
    class Meta:
        model = Prescription
        fields = ("object", "title", "description", "requires_stop", "requires_personal_recheck", "attachments", "violation_photos")
    
    def save(self, **kwargs):
        violation_photos = self.validated_data.pop("violation_photos", [])
        
        prescription = super().save(**kwargs)
        
        if violation_photos:
            from api.utils.file_storage import upload_violation_photos_base64
            from api.utils.logging import log_message, LogLevel, LogCategory

            request = self.context.get("request")
            user_name = request.user.full_name if request and request.user else "Система"
            user_role = request.user.role if request and request.user else "system"
            
            log_message(
                LogLevel.INFO, 
                LogCategory.FILE_STORAGE, 
                f"Начинаем загрузку {len(violation_photos)} фото для нарушения '{prescription.title}' (ID: {prescription.id}). Пользователь: {user_name} (роль: {user_role})"
            )
            
            urls = upload_violation_photos_base64(
                violation_photos, 
                request.user.id,
                prescription.title, 
                user_name, 
                user_role
            )
            
            if urls:
                prescription.violation_photos_folder_url = urls
                prescription.save(update_fields=["violation_photos_folder_url"])
                
                log_message(
                    LogLevel.INFO, 
                    LogCategory.FILE_STORAGE, 
                    f"Массив ссылок на фото нарушения '{prescription.title}' (ID: {prescription.id}) успешно сохранен в БД: {len(urls)} URL"
                )
            else:
                log_message(
                    LogLevel.ERROR, 
                    LogCategory.FILE_STORAGE, 
                    f"Не удалось получить URL для фото нарушения '{prescription.title}' (ID: {prescription.id}). Ссылки не сохранены в БД."
                )
        
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
    fix_photos = serializers.ListField(
        child=serializers.CharField(), 
        required=False, 
        help_text="Список фото исправления нарушения в формате base64"
    )
    
    class Meta:
        model = PrescriptionFix
        fields = ("comment", "attachments", "fix_photos")
    
    def save(self, **kwargs):
        fix_photos = self.validated_data.pop("fix_photos", [])
        
        prescription_fix = super().save(**kwargs)
        
        if fix_photos:
            from api.utils.file_storage import upload_fix_photos_base64
            request = self.context.get("request")
            user_name = request.user.full_name if request and request.user else "Система"
            user_role = request.user.role if request and request.user else "system"
            
            urls = upload_fix_photos_base64(
                fix_photos, 
                prescription_fix.prescription.id, 
                prescription_fix.prescription.object.foreman_id,
                prescription_fix.prescription.title, 
                user_name, 
                user_role
            )
            
            if urls:
                prescription_fix.fix_photos_folder_url = urls
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