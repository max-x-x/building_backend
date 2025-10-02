import requests
import json
from typing import List, Dict, Optional
from django.conf import settings
from api.utils.logging import (
    log_file_storage_connection_failed, 
    log_file_storage_timeout, 
    log_file_storage_response_error
)


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
            
        except requests.exceptions.ConnectionError as e:
            log_file_storage_connection_failed("upload_files", str(e))
            return None
        except requests.exceptions.Timeout as e:
            log_file_storage_timeout("upload_files", self.timeout)
            return None
        except requests.exceptions.HTTPError as e:
            log_file_storage_response_error("upload_files", e.response.status_code, e.response.text)
            return None
        except Exception as e:
            log_file_storage_connection_failed("upload_files", str(e))
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
            
        except requests.exceptions.ConnectionError as e:
            log_file_storage_connection_failed("create_folder", str(e))
            return None
        except requests.exceptions.Timeout as e:
            log_file_storage_timeout("create_folder", self.timeout)
            return None
        except requests.exceptions.HTTPError as e:
            log_file_storage_response_error("create_folder", e.response.status_code, e.response.text)
            return None
        except Exception as e:
            log_file_storage_connection_failed("create_folder", str(e))
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
            
        except requests.exceptions.ConnectionError as e:
            log_file_storage_connection_failed("browse_folder", str(e))
            return None
        except requests.exceptions.Timeout as e:
            log_file_storage_timeout("browse_folder", self.timeout)
            return None
        except requests.exceptions.HTTPError as e:
            log_file_storage_response_error("browse_folder", e.response.status_code, e.response.text)
            return None
        except Exception as e:
            log_file_storage_connection_failed("browse_folder", str(e))
            return None


# Глобальный экземпляр клиента
file_storage_client = FileStorageClient()


def upload_object_documents(files: List, object_id: int, object_name: str = None, user_name: str = None, user_role: str = None) -> Optional[str]:
    """
    Загружает документы объекта в файловое хранилище.
    
    Args:
        files: Список файлов документов
        object_id: ID объекта
        object_name: Название объекта (для логирования)
        user_name: Имя пользователя (для логирования)
        user_role: Роль пользователя (для логирования)
        
    Returns:
        URL папки с документами или None при ошибке
    """
    from api.utils.logging import log_object_documents_uploaded, log_object_documents_upload_failed
    
    folder_name = f"object_{object_id}_documents"
    folder_url = file_storage_client.upload_files(files, folder_name)
    
    # Логируем результат
    if folder_url:
        if object_name and user_name and user_role:
            log_object_documents_uploaded(object_name, object_id, folder_url, user_name, user_role, len(files))
    else:
        if object_name and user_name and user_role:
            log_object_documents_upload_failed(object_name, object_id, "Неизвестная ошибка", user_name, user_role, len(files))
    
    return folder_url


def upload_violation_photos(files: List, prescription_id: int, prescription_title: str = None, user_name: str = None, user_role: str = None) -> Optional[str]:
    """
    Загружает фото нарушения в файловое хранилище.
    
    Args:
        files: Список фото нарушения
        prescription_id: ID нарушения
        prescription_title: Название нарушения (для логирования)
        user_name: Имя пользователя (для логирования)
        user_role: Роль пользователя (для логирования)
        
    Returns:
        URL папки с фото или None при ошибке
    """
    from api.utils.logging import log_violation_photos_uploaded, log_violation_photos_upload_failed
    
    folder_name = f"prescription_{prescription_id}_violation_photos"
    folder_url = file_storage_client.upload_files(files, folder_name)
    
    # Логируем результат
    if folder_url:
        if prescription_title and user_name and user_role:
            log_violation_photos_uploaded(prescription_title, prescription_id, folder_url, user_name, user_role, len(files))
    else:
        if prescription_title and user_name and user_role:
            log_violation_photos_upload_failed(prescription_title, prescription_id, "Неизвестная ошибка", user_name, user_role, len(files))
    
    return folder_url


def upload_fix_photos(files: List, prescription_id: int, prescription_title: str = None, user_name: str = None, user_role: str = None) -> Optional[str]:
    """
    Загружает фото исправления нарушения в файловое хранилище.
    
    Args:
        files: Список фото исправления
        prescription_id: ID нарушения
        prescription_title: Название нарушения (для логирования)
        user_name: Имя пользователя (для логирования)
        user_role: Роль пользователя (для логирования)
        
    Returns:
        URL папки с фото или None при ошибке
    """
    from api.utils.logging import log_fix_photos_uploaded, log_fix_photos_upload_failed
    
    folder_name = f"prescription_{prescription_id}_fix_photos"
    folder_url = file_storage_client.upload_files(files, folder_name)
    
    # Логируем результат
    if folder_url:
        if prescription_title and user_name and user_role:
            log_fix_photos_uploaded(prescription_title, prescription_id, folder_url, user_name, user_role, len(files))
    else:
        if prescription_title and user_name and user_role:
            log_fix_photos_upload_failed(prescription_title, prescription_id, "Неизвестная ошибка", user_name, user_role, len(files))
    
    return folder_url


def upload_invoice_photos(files: List, delivery_id: int, user_name: str = None, user_role: str = None) -> Optional[str]:
    """
    Загружает фото накладных в файловое хранилище.
    
    Args:
        files: Список фото накладных
        delivery_id: ID поставки
        user_name: Имя пользователя (для логирования)
        user_role: Роль пользователя (для логирования)
        
    Returns:
        URL папки с фото или None при ошибке
    """
    from api.utils.logging import log_invoice_photos_uploaded, log_invoice_photos_upload_failed
    
    folder_name = f"delivery_{delivery_id}_invoice_photos"
    folder_url = file_storage_client.upload_files(files, folder_name)
    
    # Логируем результат
    if folder_url:
        if user_name and user_role:
            log_invoice_photos_uploaded(delivery_id, folder_url, user_name, user_role, len(files))
    else:
        if user_name and user_role:
            log_invoice_photos_upload_failed(delivery_id, "Неизвестная ошибка", user_name, user_role, len(files))
    
    return folder_url
