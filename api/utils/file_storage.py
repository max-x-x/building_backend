import requests
import json
from typing import List, Dict, Optional
from django.conf import settings


class FileStorageClient:
    """Клиент для работы с файловым хранилищем."""
    
    def __init__(self):
        self.base_url = getattr(settings, 'FILE_STORAGE_URL', 'https://building-s3-api.itc-hub.ru')
        self.timeout = 30
    
    def upload_files(self, files: List, folder_name: str = None) -> Optional[str]:
        """
        Загружает файлы в файловое хранилище.
        
        Args:
            files: Список файлов для загрузки
            folder_name: Имя папки (опционально)
            
        Returns:
            URL созданной папки или None при ошибке
        """
        try:
            url = f"{self.base_url}/upload"
            
            # Подготавливаем данные для загрузки
            data = {}
            if folder_name:
                data['folder_name'] = folder_name
            
            # Подготавливаем файлы
            files_data = []
            for file in files:
                files_data.append(('files', file))
            
            response = requests.post(
                url, 
                data=data, 
                files=files_data,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get('folder_url') or result.get('url')
            
        except Exception as e:
            print(f"Ошибка загрузки файлов: {e}")
            return None
    
    def create_folder(self, folder_name: str) -> Optional[str]:
        """
        Создает папку в файловом хранилище.
        
        Args:
            folder_name: Имя папки
            
        Returns:
            URL созданной папки или None при ошибке
        """
        try:
            url = f"{self.base_url}/create-folder"
            
            data = {
                'folder_name': folder_name
            }
            
            response = requests.post(
                url, 
                json=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get('folder_url')
            
        except Exception as e:
            print(f"Ошибка создания папки: {e}")
            return None
    
    def browse_folder(self, folder_url: str) -> Optional[List[Dict]]:
        """
        Получает список файлов в папке.
        
        Args:
            folder_url: URL папки
            
        Returns:
            Список файлов или None при ошибке
        """
        try:
            url = f"{self.base_url}/browse"
            
            data = {
                'folder_url': folder_url
            }
            
            response = requests.post(
                url, 
                json=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get('files', [])
            
        except Exception as e:
            print(f"Ошибка получения списка файлов: {e}")
            return None


# Глобальный экземпляр клиента
file_storage_client = FileStorageClient()


def upload_object_documents(files: List, object_id: int) -> Optional[str]:
    """
    Загружает документы объекта в файловое хранилище.
    
    Args:
        files: Список файлов документов
        object_id: ID объекта
        
    Returns:
        URL папки с документами или None при ошибке
    """
    folder_name = f"object_{object_id}_documents"
    return file_storage_client.upload_files(files, folder_name)


def upload_violation_photos(files: List, prescription_id: int) -> Optional[str]:
    """
    Загружает фото нарушения в файловое хранилище.
    
    Args:
        files: Список фото нарушения
        prescription_id: ID нарушения
        
    Returns:
        URL папки с фото или None при ошибке
    """
    folder_name = f"prescription_{prescription_id}_violation_photos"
    return file_storage_client.upload_files(files, folder_name)


def upload_fix_photos(files: List, prescription_id: int) -> Optional[str]:
    """
    Загружает фото исправления нарушения в файловое хранилище.
    
    Args:
        files: Список фото исправления
        prescription_id: ID нарушения
        
    Returns:
        URL папки с фото или None при ошибке
    """
    folder_name = f"prescription_{prescription_id}_fix_photos"
    return file_storage_client.upload_files(files, folder_name)


def upload_invoice_photos(files: List, delivery_id: int) -> Optional[str]:
    """
    Загружает фото накладных в файловое хранилище.
    
    Args:
        files: Список фото накладных
        delivery_id: ID поставки
        
    Returns:
        URL папки с фото или None при ошибке
    """
    folder_name = f"delivery_{delivery_id}_invoice_photos"
    return file_storage_client.upload_files(files, folder_name)
