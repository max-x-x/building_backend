from rest_framework import serializers
from api.models.prescription import Prescription, PrescriptionFix
from api.serializers.objects import ObjectShortSerializer


class PrescriptionCreateSerializer(serializers.ModelSerializer):
    # фото нарушения в формате base64 (принимаются с фронта)
    violation_photos = serializers.ListField(
        child=serializers.CharField(), 
        required=False, 
        help_text="Список фото нарушения в формате base64"
    )
    
    class Meta:
        model = Prescription
        fields = ("object", "title", "description", "requires_stop", "requires_personal_recheck", "attachments", "violation_photos")
    
    def save(self, **kwargs):
        # Извлекаем violation_photos из validated_data, так как это поле не существует в модели
        violation_photos = self.validated_data.pop("violation_photos", [])
        
        # Создаем нарушение с дополнительными параметрами
        prescription = super().save(**kwargs)
        
        # Загружаем фото в файловое хранилище
        if violation_photos:
            from api.utils.file_storage import upload_violation_photos_base64
            from api.utils.logging import log_message, LogLevel, LogCategory
            
            # Получаем информацию о пользователе из контекста
            request = self.context.get("request")
            user_name = request.user.full_name if request and request.user else "Система"
            user_role = request.user.role if request and request.user else "system"
            
            # Логируем начало загрузки
            log_message(
                LogLevel.INFO, 
                LogCategory.FILE_STORAGE, 
                f"Начинаем загрузку {len(violation_photos)} фото для нарушения '{prescription.title}' (ID: {prescription.id}). Пользователь: {user_name} (роль: {user_role})"
            )
            
            # Загружаем фото и получаем массив URL
            urls = upload_violation_photos_base64(
                violation_photos, 
                request.user.id,
                prescription.title, 
                user_name, 
                user_role
            )
            
            if urls:
                # Сохраняем массив ссылок на фото
                prescription.violation_photos_folder_url = urls
                prescription.save(update_fields=["violation_photos_folder_url"])
                
                # Логируем успешное сохранение
                log_message(
                    LogLevel.INFO, 
                    LogCategory.FILE_STORAGE, 
                    f"Массив ссылок на фото нарушения '{prescription.title}' (ID: {prescription.id}) успешно сохранен в БД: {len(urls)} URL"
                )
            else:
                # Логируем ошибку
                log_message(
                    LogLevel.ERROR, 
                    LogCategory.FILE_STORAGE, 
                    f"Не удалось получить URL для фото нарушения '{prescription.title}' (ID: {prescription.id}). Ссылки не сохранены в БД."
                )
        
        return prescription

class PrescriptionOutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prescription
        fields = "__all__"

class PrescriptionFixCreateSerializer(serializers.ModelSerializer):
    # фото исправления в формате base64 (принимаются с фронта)
    fix_photos = serializers.ListField(
        child=serializers.CharField(), 
        required=False, 
        help_text="Список фото исправления нарушения в формате base64"
    )
    
    class Meta:
        model = PrescriptionFix
        fields = ("comment", "attachments", "fix_photos")
    
    def save(self, **kwargs):
        # Извлекаем fix_photos из validated_data, так как это поле не существует в модели
        fix_photos = self.validated_data.pop("fix_photos", [])
        
        # Создаем исправление с дополнительными параметрами
        prescription_fix = super().save(**kwargs)
        
        # Загружаем фото в файловое хранилище
        if fix_photos:
            from api.utils.file_storage import upload_fix_photos_base64
            
            # Получаем информацию о пользователе из контекста
            request = self.context.get("request")
            user_name = request.user.full_name if request and request.user else "Система"
            user_role = request.user.role if request and request.user else "system"
            
            # Загружаем фото и получаем массив URL
            urls = upload_fix_photos_base64(
                fix_photos, 
                prescription_fix.prescription.id, 
                prescription_fix.prescription.object.foreman_id,  # Добавляем foreman_id
                prescription_fix.prescription.title, 
                user_name, 
                user_role
            )
            
            if urls:
                # Сохраняем массив ссылок на фото
                prescription_fix.fix_photos_folder_url = urls
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