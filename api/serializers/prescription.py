from rest_framework import serializers
from api.models.prescription import Prescription, PrescriptionFix
from api.serializers.objects import ObjectShortSerializer


class PrescriptionCreateSerializer(serializers.ModelSerializer):
    # фото нарушения (принимаются с фронта)
    violation_photos = serializers.ListField(
        child=serializers.FileField(), 
        required=False, 
        help_text="Список фото нарушения"
    )
    
    class Meta:
        model = Prescription
        fields = ("object", "title", "description", "requires_stop", "requires_personal_recheck", "attachments", "violation_photos")
    
    def create(self, validated_data):
        violation_photos = validated_data.pop("violation_photos", [])
        
        # Создаем нарушение
        prescription = super().create(validated_data)
        
        # Загружаем фото в файловое хранилище
        if violation_photos:
            from api.utils.file_storage import upload_violation_photos
            
            # Получаем информацию о пользователе из контекста
            request = self.context.get("request")
            user_name = request.user.full_name if request and request.user else "Система"
            user_role = request.user.role if request and request.user else "system"
            
            # Загружаем фото и получаем URL папки
            folder_url = upload_violation_photos(
                violation_photos, 
                prescription.id, 
                prescription.title, 
                user_name, 
                user_role
            )
            
            if folder_url:
                # Сохраняем ссылку на папку с фото
                prescription.violation_photos_folder_url = folder_url
                prescription.save(update_fields=["violation_photos_folder_url"])
        
        return prescription

class PrescriptionOutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prescription
        fields = "__all__"

class PrescriptionFixCreateSerializer(serializers.ModelSerializer):
    # фото исправления (принимаются с фронта)
    fix_photos = serializers.ListField(
        child=serializers.FileField(), 
        required=False, 
        help_text="Список фото исправления нарушения"
    )
    
    class Meta:
        model = PrescriptionFix
        fields = ("comment", "attachments", "fix_photos")
    
    def create(self, validated_data):
        fix_photos = validated_data.pop("fix_photos", [])
        
        # Создаем исправление
        prescription_fix = super().create(validated_data)
        
        # Загружаем фото в файловое хранилище
        if fix_photos:
            from api.utils.file_storage import upload_fix_photos
            
            # Получаем информацию о пользователе из контекста
            request = self.context.get("request")
            user_name = request.user.full_name if request and request.user else "Система"
            user_role = request.user.role if request and request.user else "system"
            
            # Загружаем фото и получаем URL папки
            folder_url = upload_fix_photos(
                fix_photos, 
                prescription_fix.prescription.id, 
                prescription_fix.prescription.object.foreman_id,  # Добавляем foreman_id
                prescription_fix.prescription.title, 
                user_name, 
                user_role
            )
            
            if folder_url:
                # Сохраняем ссылку на папку с фото
                prescription_fix.fix_photos_folder_url = folder_url
                prescription_fix.save(update_fields=["fix_photos_folder_url"])
        
        return prescription_fix

class PrescriptionListSerializer(serializers.ModelSerializer):
    object = ObjectShortSerializer(read_only=True)

    class Meta:
        model = Prescription
        fields = (
            "id", "uuid_prescription",
            "object", "author", "title",
            "requires_stop", "requires_personal_recheck", "description",
            "status", "violation_photos_folder_url", "created_at", "closed_at",
        )