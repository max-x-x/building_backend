import base64
import mimetypes
from typing import List, Dict, Optional, Union, Tuple, Any
from datetime import date as dt_date

import requests
from django.conf import settings

from api.utils.logging import (
    log_file_storage_connection_failed,
    log_file_storage_timeout,
    log_file_storage_response_error,
)


Readable = Union[bytes, str, Any]  # Любой файловый объект


class FileStorageClient:
    """
    Клиент для работы с твоим S3/MinIO media сервисом.

    Эндпоинты:
      - POST /upload/docs/object/{object_id}                  (multipart PDF)
      - POST /upload/foreman/visit/{foreman_id}               (JSON {photos_base64[, date]})
      - POST /upload/violation/{tag}/{entity_id}/creation     (JSON {photos_base64[, date]})
      - POST /upload/violation/{violation_id}/correction/by-foreman/{foreman_id} (JSON {photos_base64[, date]})
      - POST /upload/delivery/{object_id}/{delivery_id}       (JSON {photos_base64[, date]})

    Обход (browse):
      - GET  /browse/object/{object_id}
      - GET  /browse/foreman/{foreman_id}
      - GET  /browse/violation/{tag}/{entity_id}
    """

    def __init__(self):
        self.base_url: str = getattr(settings, "FILE_STORAGE_URL", "https://building-s3-api.itc-hub.ru").rstrip("/")
        # токен можно хранить в любом из этих настроек — возьмём что найдём
        self.token: Optional[str] = (
            getattr(settings, "FILE_STORAGE_TOKEN", None)
            or getattr(settings, "FILE_STORAGE_UPLOAD_TOKEN", None)
            or getattr(settings, "S3_MEDIA_UPLOAD_TOKEN", None)
        )
        self.timeout: int = int(getattr(settings, "FILE_STORAGE_TIMEOUT", 30))
        self.session = requests.Session()

    # --------------------------- helpers ---------------------------

    def _headers(self) -> Dict[str, str]:
        if not self.token:
            return {}
        return {
            "X-API-Token": self.token,
            "Authorization": f"Bearer {self.token}",
        }

    @staticmethod
    def _ensure_iso_date(d: Optional[Union[str, dt_date]]) -> Optional[str]:
        if d is None:
            return None
        if isinstance(d, str):
            return d  # ожидается YYYY-MM-DD
        return d.isoformat()

    @staticmethod
    def _read_bytes(file: Readable) -> Tuple[bytes, Optional[str], Optional[str]]:
        """
        Универсально читаем содержимое и пытаемся понять имя/контент-тайп.
        Возвращает (data, filename, content_type).
        """
        filename: Optional[str] = None
        content_type: Optional[str] = None

        # путь на диске
        if isinstance(file, str):
            filename = file
            with open(file, "rb") as f:
                data = f.read()
            content_type = mimetypes.guess_type(filename)[0] or None
            return data, filename, content_type

        # «сырые» байты
        if isinstance(file, (bytes, bytearray)):
            return bytes(file), None, None

        # file-like (InMemoryUploadedFile/TemporaryUploadedFile/BytesIO и т.п.)
        # у Django-файлов есть .name и .content_type
        try:
            if hasattr(file, "name"):
                filename = getattr(file, "name")
            if hasattr(file, "content_type"):
                content_type = getattr(file, "content_type")
            # читаем
            if hasattr(file, "seek"):
                file.seek(0)
            data = file.read()
            return data, filename, content_type
        except Exception:
            # как крайний случай — попробуем .read() напрямую
            data = file.read()
            return data, filename, content_type

    @staticmethod
    def _to_data_url(data: bytes, mime: Optional[str], fallback: str = "image/jpeg") -> str:
        mt = (mime or fallback).lower()
        b64 = base64.b64encode(data).decode("ascii")
        return f"data:{mt};base64,{b64}"

    def _encode_images(self, files: List[Readable]) -> List[str]:
        """
        Готовит массив data URL (base64) для JSON ручек.
        """
        out: List[str] = []
        for f in files:
            data, filename, content_type = self._read_bytes(f)
            # если тип не известен — пробуем угадать по расширению
            if not content_type and filename:
                content_type = mimetypes.guess_type(filename)[0] or None
            # ограничим поддерживаемое (сервер прозрачно примет и другие, но лучше явно)
            if content_type not in {"image/jpeg", "image/jpg", "image/png", "image/webp", "image/heic", "image/heif"}:
                content_type = "image/jpeg"
            out.append(self._to_data_url(data, content_type))
        return out

    # --------------------------- uploads ---------------------------

    def upload_object_pdf(self, object_id: Union[int, str], file: Readable) -> Optional[Dict]:
        """
        POST /upload/docs/object/{object_id}
        Multipart поле: file
        Возвращает UploadedFile (dict) или None при ошибке.
        """
        url = f"{self.base_url}/upload/docs/object/{object_id}"
        try:
            data, filename, content_type = self._read_bytes(file)
            content_type = content_type or "application/pdf"
            filename = (filename or "document.pdf").rsplit("/", 1)[-1]

            files = {
                "file": (filename, data, content_type),
            }

            resp = self.session.post(url, headers=self._headers(), files=files, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.ConnectionError as e:
            log_file_storage_connection_failed("upload_object_pdf", str(e))
        except requests.exceptions.Timeout:
            log_file_storage_timeout("upload_object_pdf", self.timeout)
        except requests.exceptions.HTTPError as e:
            log_file_storage_response_error("upload_object_pdf", e.response.status_code, e.response.text)
        except Exception as e:
            log_file_storage_connection_failed("upload_object_pdf", str(e))
        return None

    def upload_foreman_visit(
        self,
        foreman_id: Union[int, str],
        images: List[Readable],
        date: Optional[Union[str, dt_date]] = None,
    ) -> Optional[Dict]:
        """
        POST /upload/foreman/visit/{foreman_id}
        JSON: { "photos_base64": [...], "date": "YYYY-MM-DD" (необязательно) }
        """
        url = f"{self.base_url}/upload/foreman/visit/{foreman_id}"
        payload: Dict = {"photos_base64": self._encode_images(images)}
        iso = self._ensure_iso_date(date)
        if iso:
            payload["date"] = iso

        try:
            resp = self.session.post(url, headers=self._headers(), json=payload, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.ConnectionError as e:
            log_file_storage_connection_failed("upload_foreman_visit", str(e))
        except requests.exceptions.Timeout:
            log_file_storage_timeout("upload_foreman_visit", self.timeout)
        except requests.exceptions.HTTPError as e:
            log_file_storage_response_error("upload_foreman_visit", e.response.status_code, e.response.text)
        except Exception as e:
            log_file_storage_connection_failed("upload_foreman_visit", str(e))
        return None

    def upload_violation_creation(
        self,
        tag: str,  # "ССК" | "ИКО"
        entity_id: Union[int, str],
        images: List[Readable],
        date: Optional[Union[str, dt_date]] = None,
    ) -> Optional[Dict]:
        """
        POST /upload/violation/{tag}/{entity_id}/creation
        JSON: { "photos_base64": [...], "date": "YYYY-MM-DD" (необязательно) }
        """
        url = f"{self.base_url}/upload/violation/{tag}/{entity_id}/creation"
        payload: Dict = {"photos_base64": self._encode_images(images)}
        iso = self._ensure_iso_date(date)
        if iso:
            payload["date"] = iso

        try:
            resp = self.session.post(url, headers=self._headers(), json=payload, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.ConnectionError as e:
            log_file_storage_connection_failed("upload_violation_creation", str(e))
        except requests.exceptions.Timeout:
            log_file_storage_timeout("upload_violation_creation", self.timeout)
        except requests.exceptions.HTTPError as e:
            log_file_storage_response_error("upload_violation_creation", e.response.status_code, e.response.text)
        except Exception as e:
            log_file_storage_connection_failed("upload_violation_creation", str(e))
        return None

    def upload_violation_correction(
        self,
        violation_id: Union[int, str],
        foreman_id: Union[int, str],
        images: List[Readable],
        date: Optional[Union[str, dt_date]] = None,
    ) -> Optional[Dict]:
        """
        POST /upload/violation/{violation_id}/correction/by-foreman/{foreman_id}
        JSON: { "photos_base64": [...], "date": "YYYY-MM-DD" (необязательно) }
        """
        url = f"{self.base_url}/upload/violation/{violation_id}/correction/by-foreman/{foreman_id}"
        payload: Dict = {"photos_base64": self._encode_images(images)}
        iso = self._ensure_iso_date(date)
        if iso:
            payload["date"] = iso

        try:
            resp = self.session.post(url, headers=self._headers(), json=payload, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.ConnectionError as e:
            log_file_storage_connection_failed("upload_violation_correction", str(e))
        except requests.exceptions.Timeout:
            log_file_storage_timeout("upload_violation_correction", self.timeout)
        except requests.exceptions.HTTPError as e:
            log_file_storage_response_error("upload_violation_correction", e.response.status_code, e.response.text)
        except Exception as e:
            log_file_storage_connection_failed("upload_violation_correction", str(e))
        return None

    def upload_delivery_photos(
        self,
        object_id: Union[int, str],
        delivery_id: Union[int, str],
        images: List[Readable],
        date: Optional[Union[str, dt_date]] = None,
    ) -> Optional[Dict]:
        """
        POST /upload/delivery/{object_id}/{delivery_id}
        JSON: { "photos_base64": [...], "date": "YYYY-MM-DD" (необязательно) }
        """
        url = f"{self.base_url}/upload/delivery/{object_id}/{delivery_id}"
        payload: Dict = {"photos_base64": self._encode_images(images)}
        iso = self._ensure_iso_date(date)
        if iso:
            payload["date"] = iso

        try:
            resp = self.session.post(url, headers=self._headers(), json=payload, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.ConnectionError as e:
            log_file_storage_connection_failed("upload_delivery_photos", str(e))
        except requests.exceptions.Timeout:
            log_file_storage_timeout("upload_delivery_photos", self.timeout)
        except requests.exceptions.HTTPError as e:
            log_file_storage_response_error("upload_delivery_photos", e.response.status_code, e.response.text)
        except Exception as e:
            log_file_storage_connection_failed("upload_delivery_photos", str(e))
        return None

    # --------------------------- browse ---------------------------

    def browse_object(self, object_id: Union[int, str]) -> Optional[Dict]:
        """
        GET /browse/object/{object_id}
        Возвращает:
        {
          "object_id": "...",
          "documentation": TreeNode,
          "deliveries": TreeNode
        }
        """
        url = f"{self.base_url}/browse/object/{object_id}"
        try:
            resp = self.session.get(url, headers=self._headers(), timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.ConnectionError as e:
            log_file_storage_connection_failed("browse_object", str(e))
        except requests.exceptions.Timeout:
            log_file_storage_timeout("browse_object", self.timeout)
        except requests.exceptions.HTTPError as e:
            log_file_storage_response_error("browse_object", e.response.status_code, e.response.text)
        except Exception as e:
            log_file_storage_connection_failed("browse_object", str(e))
        return None

    def browse_foreman(self, foreman_id: Union[int, str]) -> Optional[Dict]:
        """
        GET /browse/foreman/{foreman_id}
        Возвращает TreeNode
        """
        url = f"{self.base_url}/browse/foreman/{foreman_id}"
        try:
            resp = self.session.get(url, headers=self._headers(), timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.ConnectionError as e:
            log_file_storage_connection_failed("browse_foreman", str(e))
        except requests.exceptions.Timeout:
            log_file_storage_timeout("browse_foreman", self.timeout)
        except requests.exceptions.HTTPError as e:
            log_file_storage_response_error("browse_foreman", e.response.status_code, e.response.text)
        except Exception as e:
            log_file_storage_connection_failed("browse_foreman", str(e))
        return None

    def browse_violation(self, tag: str, entity_id: Union[int, str]) -> Optional[Dict]:
        """
        GET /browse/violation/{tag}/{entity_id}
        Возвращает TreeNode
        """
        url = f"{self.base_url}/browse/violation/{tag}/{entity_id}"
        try:
            resp = self.session.get(url, headers=self._headers(), timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.ConnectionError as e:
            log_file_storage_connection_failed("browse_violation", str(e))
        except requests.exceptions.Timeout:
            log_file_storage_timeout("browse_violation", self.timeout)
        except requests.exceptions.HTTPError as e:
            log_file_storage_response_error("browse_violation", e.response.status_code, e.response.text)
        except Exception as e:
            log_file_storage_connection_failed("browse_violation", str(e))
        return None


# Глобальный экземпляр клиента
file_storage_client = FileStorageClient()


# === ФУНКЦИИ-ОБЕРТКИ ДЛЯ ИНТЕГРАЦИИ С API ===

def upload_object_documents_base64(base64_files: List[str], object_id: int, object_name: str = None, user_name: str = None, user_role: str = None) -> Optional[List[str]]:
    """
    Загружает документы объекта в файловое хранилище из base64.
    Использует upload_object_pdf для каждого файла.
    Возвращает список URL всех загруженных файлов.
    """
    from api.utils.logging import log_object_documents_uploaded, log_object_documents_upload_failed
    
    uploaded_urls = []
    
    for i, base64_data in enumerate(base64_files):
        # Декодируем base64 в байты
        try:
            import base64
            # Убираем префикс data:image/...;base64, если есть
            if ',' in base64_data:
                base64_data = base64_data.split(',', 1)[1]
            # Добавляем padding если необходимо
            missing_padding = len(base64_data) % 4
            if missing_padding:
                base64_data += '=' * (4 - missing_padding)
            file_data = base64.b64decode(base64_data)
            result = file_storage_client.upload_object_pdf(object_id, file_data)
            if result and result.get('files') and len(result['files']) > 0:
                # Получаем URL из первого файла (может быть url или presigned_url)
                file_info = result['files'][0]
                file_url = file_info.get('url') or file_info.get('presigned_url')
                if file_url:
                    uploaded_urls.append(file_url)
        except Exception as e:
            from api.utils.logging import log_message, LogLevel, LogCategory
            log_message(LogLevel.ERROR, LogCategory.FILE_STORAGE, f"Ошибка декодирования base64 файла {i+1}: {str(e)}")
    
    # Логируем результат
    if uploaded_urls:
        if object_name and user_name and user_role:
            log_object_documents_uploaded(object_name, object_id, f"{len(uploaded_urls)} файлов", user_name, user_role, len(base64_files))
        return uploaded_urls
    else:
        if object_name and user_name and user_role:
            log_object_documents_upload_failed(object_name, object_id, "Не удалось загрузить файлы", user_name, user_role, len(base64_files))
        return None


def upload_object_documents(files: List[Readable], object_id: int, object_name: str = None, user_name: str = None, user_role: str = None) -> Optional[str]:
    """
    Загружает документы объекта в файловое хранилище.
    Использует upload_object_pdf для каждого файла.
    """
    from api.utils.logging import log_object_documents_uploaded, log_object_documents_upload_failed
    
    uploaded_urls = []
    
    for file in files:
        result = file_storage_client.upload_object_pdf(object_id, file)
        if result and result.get('url'):
            uploaded_urls.append(result['url'])
    
    # Логируем результат
    if uploaded_urls:
        folder_url = uploaded_urls[0] if len(uploaded_urls) == 1 else f"{len(uploaded_urls)} файлов загружено"
        if object_name and user_name and user_role:
            log_object_documents_uploaded(object_name, object_id, folder_url, user_name, user_role, len(files))
        return folder_url
    else:
        if object_name and user_name and user_role:
            log_object_documents_upload_failed(object_name, object_id, "Не удалось загрузить файлы", user_name, user_role, len(files))
        return None


def upload_violation_photos_base64(base64_files: List[str], prescription_id: int, prescription_title: str = None, user_name: str = None, user_role: str = None) -> Optional[List[str]]:
    """
    Загружает фото нарушения в файловое хранилище из base64.
    Использует upload_violation_creation для каждого файла.
    Возвращает список URL всех загруженных файлов.
    """
    from api.utils.logging import log_violation_photos_uploaded, log_violation_photos_upload_failed, log_message, LogLevel, LogCategory
    
    # Определяем тег по роли пользователя
    tag = "ССК" if user_role == "ssk" else "ИКО" if user_role == "iko" else "ССК"
    
    # Логируем начало процесса
    log_message(
        LogLevel.INFO, 
        LogCategory.FILE_STORAGE, 
        f"Начинаем загрузку фото нарушения из base64. Тег: {tag}, prescription_id: {prescription_id}, файлов: {len(base64_files)}. URL хранилища: {file_storage_client.base_url}"
    )
    
    uploaded_urls = []
    
    for i, base64_data in enumerate(base64_files):
        log_message(
            LogLevel.INFO, 
            LogCategory.FILE_STORAGE, 
            f"Загружаем файл {i+1}/{len(base64_files)} для нарушения {prescription_id}"
        )
        
        # Декодируем base64 в байты
        try:
            import base64
            # Убираем префикс data:image/...;base64, если есть
            if ',' in base64_data:
                base64_data = base64_data.split(',', 1)[1]
            # Добавляем padding если необходимо
            missing_padding = len(base64_data) % 4
            if missing_padding:
                base64_data += '=' * (4 - missing_padding)
            file_data = base64.b64decode(base64_data)
            result = file_storage_client.upload_violation_creation(tag, prescription_id, [file_data])
            
            if result and result.get('files') and len(result['files']) > 0:
                # Получаем URL из первого файла (может быть url или presigned_url)
                file_info = result['files'][0]
                file_url = file_info.get('url') or file_info.get('presigned_url')
                if file_url:
                    uploaded_urls.append(file_url)
                    log_message(
                        LogLevel.INFO, 
                        LogCategory.FILE_STORAGE, 
                        f"Файл {i+1} успешно загружен для нарушения {prescription_id}. URL: {file_url}"
                    )
                else:
                    log_message(
                        LogLevel.ERROR, 
                        LogCategory.FILE_STORAGE, 
                        f"Файл {i+1} загружен для нарушения {prescription_id}, но URL не найден. Результат: {result}"
                    )
            else:
                log_message(
                    LogLevel.ERROR, 
                    LogCategory.FILE_STORAGE, 
                    f"Ошибка загрузки файла {i+1} для нарушения {prescription_id}. Результат: {result}"
                )
        except Exception as e:
            log_message(
                LogLevel.ERROR, 
                LogCategory.FILE_STORAGE, 
                f"Ошибка декодирования base64 файла {i+1} для нарушения {prescription_id}: {str(e)}"
            )
    
    # Логируем итоговый результат
    if uploaded_urls:
        if prescription_title and user_name and user_role:
            log_violation_photos_uploaded(prescription_title, prescription_id, f"{len(uploaded_urls)} файлов", user_name, user_role, len(base64_files))
        
        log_message(
            LogLevel.INFO, 
            LogCategory.FILE_STORAGE, 
            f"Загрузка фото нарушения {prescription_id} завершена успешно. Загружено: {len(uploaded_urls)}/{len(base64_files)} файлов. Возвращаем массив из {len(uploaded_urls)} URL"
        )
        return uploaded_urls
    else:
        if prescription_title and user_name and user_role:
            log_violation_photos_upload_failed(prescription_title, prescription_id, "Не удалось загрузить файлы", user_name, user_role, len(base64_files))
        
        log_message(
            LogLevel.ERROR, 
            LogCategory.FILE_STORAGE, 
            f"Загрузка фото нарушения {prescription_id} завершилась неудачей. Ни один файл не был загружен из {len(base64_files)} файлов."
        )
        return None


def upload_violation_photos(files: List[Readable], prescription_id: int, prescription_title: str = None, user_name: str = None, user_role: str = None) -> Optional[str]:
    """
    Загружает фото нарушения в файловое хранилище.
    Использует upload_violation_creation для каждого файла.
    """
    from api.utils.logging import log_violation_photos_uploaded, log_violation_photos_upload_failed, log_message, LogLevel, LogCategory
    
    # Определяем тег по роли пользователя
    tag = "ССК" if user_role == "ssk" else "ИКО" if user_role == "iko" else "ССК"
    
    # Логируем начало процесса
    log_message(
        LogLevel.INFO, 
        LogCategory.FILE_STORAGE, 
        f"Начинаем загрузку фото нарушения. Тег: {tag}, prescription_id: {prescription_id}, файлов: {len(files)}. URL хранилища: {file_storage_client.base_url}"
    )
    
    uploaded_urls = []
    
    for i, file in enumerate(files):
        log_message(
            LogLevel.INFO, 
            LogCategory.FILE_STORAGE, 
            f"Загружаем файл {i+1}/{len(files)} для нарушения {prescription_id}"
        )
        
        result = file_storage_client.upload_violation_creation(tag, prescription_id, [file])
        
        if result and result.get('url'):
            uploaded_urls.append(result['url'])
            log_message(
                LogLevel.INFO, 
                LogCategory.FILE_STORAGE, 
                f"Файл {i+1} успешно загружен для нарушения {prescription_id}. URL: {result['url']}"
            )
        else:
            log_message(
                LogLevel.ERROR, 
                LogCategory.FILE_STORAGE, 
                f"Ошибка загрузки файла {i+1} для нарушения {prescription_id}. Результат: {result}"
            )
    
    # Логируем итоговый результат
    if uploaded_urls:
        folder_url = uploaded_urls[0] if len(uploaded_urls) == 1 else f"{len(uploaded_urls)} файлов загружено"
        if prescription_title and user_name and user_role:
            log_violation_photos_uploaded(prescription_title, prescription_id, folder_url, user_name, user_role, len(files))
        
        log_message(
            LogLevel.INFO, 
            LogCategory.FILE_STORAGE, 
            f"Загрузка фото нарушения {prescription_id} завершена успешно. Загружено: {len(uploaded_urls)}/{len(files)} файлов. Возвращаем: {folder_url}"
        )
        return folder_url
    else:
        if prescription_title and user_name and user_role:
            log_violation_photos_upload_failed(prescription_title, prescription_id, "Не удалось загрузить файлы", user_name, user_role, len(files))
        
        log_message(
            LogLevel.ERROR, 
            LogCategory.FILE_STORAGE, 
            f"Загрузка фото нарушения {prescription_id} завершилась неудачей. Ни один файл не был загружен из {len(files)} файлов."
        )
        return None


def upload_fix_photos_base64(base64_files: List[str], prescription_id: int, foreman_id: int, prescription_title: str = None, user_name: str = None, user_role: str = None) -> Optional[List[str]]:
    """
    Загружает фото исправления нарушения в файловое хранилище из base64.
    Использует upload_violation_correction для каждого файла.
    Возвращает список URL всех загруженных файлов.
    """
    from api.utils.logging import log_fix_photos_uploaded, log_fix_photos_upload_failed, log_message, LogLevel, LogCategory
    
    # Логируем начало процесса
    log_message(
        LogLevel.INFO, 
        LogCategory.FILE_STORAGE, 
        f"Начинаем загрузку фото исправления из base64. prescription_id: {prescription_id}, foreman_id: {foreman_id}, файлов: {len(base64_files)}. URL хранилища: {file_storage_client.base_url}"
    )
    
    uploaded_urls = []
    
    for i, base64_data in enumerate(base64_files):
        log_message(
            LogLevel.INFO, 
            LogCategory.FILE_STORAGE, 
            f"Загружаем файл {i+1}/{len(base64_files)} для исправления нарушения {prescription_id}"
        )
        
        # Декодируем base64 в байты
        try:
            import base64
            # Убираем префикс data:image/...;base64, если есть
            if ',' in base64_data:
                base64_data = base64_data.split(',', 1)[1]
            # Добавляем padding если необходимо
            missing_padding = len(base64_data) % 4
            if missing_padding:
                base64_data += '=' * (4 - missing_padding)
            file_data = base64.b64decode(base64_data)
            result = file_storage_client.upload_violation_correction(prescription_id, foreman_id, [file_data])
            
            if result and result.get('files') and len(result['files']) > 0:
                # Получаем URL из первого файла (может быть url или presigned_url)
                file_info = result['files'][0]
                file_url = file_info.get('url') or file_info.get('presigned_url')
                if file_url:
                    uploaded_urls.append(file_url)
                    log_message(
                        LogLevel.INFO, 
                        LogCategory.FILE_STORAGE, 
                        f"Файл {i+1} успешно загружен для исправления нарушения {prescription_id}. URL: {file_url}"
                    )
                else:
                    log_message(
                        LogLevel.ERROR, 
                        LogCategory.FILE_STORAGE, 
                        f"Файл {i+1} загружен для исправления нарушения {prescription_id}, но URL не найден. Результат: {result}"
                    )
            else:
                log_message(
                    LogLevel.ERROR, 
                    LogCategory.FILE_STORAGE, 
                    f"Ошибка загрузки файла {i+1} для исправления нарушения {prescription_id}. Результат: {result}"
                )
        except Exception as e:
            log_message(
                LogLevel.ERROR, 
                LogCategory.FILE_STORAGE, 
                f"Ошибка декодирования base64 файла {i+1} для исправления нарушения {prescription_id}: {str(e)}"
            )
    
    # Логируем итоговый результат
    if uploaded_urls:
        if prescription_title and user_name and user_role:
            log_fix_photos_uploaded(prescription_title, prescription_id, f"{len(uploaded_urls)} файлов", user_name, user_role, len(base64_files))
        
        log_message(
            LogLevel.INFO, 
            LogCategory.FILE_STORAGE, 
            f"Загрузка фото исправления нарушения {prescription_id} завершена успешно. Загружено: {len(uploaded_urls)}/{len(base64_files)} файлов. Возвращаем массив из {len(uploaded_urls)} URL"
        )
        return uploaded_urls
    else:
        if prescription_title and user_name and user_role:
            log_fix_photos_upload_failed(prescription_title, prescription_id, "Не удалось загрузить файлы", user_name, user_role, len(base64_files))
        
        log_message(
            LogLevel.ERROR, 
            LogCategory.FILE_STORAGE, 
            f"Загрузка фото исправления нарушения {prescription_id} завершилась неудачей. Ни один файл не был загружен из {len(base64_files)} файлов."
        )
        return None


def upload_fix_photos(files: List[Readable], prescription_id: int, foreman_id: int, prescription_title: str = None, user_name: str = None, user_role: str = None) -> Optional[str]:
    """
    Загружает фото исправления нарушения в файловое хранилище.
    Использует upload_violation_correction для каждого файла.
    """
    from api.utils.logging import log_fix_photos_uploaded, log_fix_photos_upload_failed
    
    uploaded_urls = []
    
    for file in files:
        result = file_storage_client.upload_violation_correction(prescription_id, foreman_id, [file])
        if result and result.get('url'):
            uploaded_urls.append(result['url'])
    
    # Логируем результат
    if uploaded_urls:
        folder_url = uploaded_urls[0] if len(uploaded_urls) == 1 else f"{len(uploaded_urls)} файлов загружено"
        if prescription_title and user_name and user_role:
            log_fix_photos_uploaded(prescription_title, prescription_id, folder_url, user_name, user_role, len(files))
        return folder_url
    else:
        if prescription_title and user_name and user_role:
            log_fix_photos_upload_failed(prescription_title, prescription_id, "Не удалось загрузить файлы", user_name, user_role, len(files))
        return None


def upload_invoice_photos_base64(base64_files: List[str], object_id: int, delivery_id: int, user_name: str = None, user_role: str = None) -> Optional[List[str]]:
    """
    Загружает фото накладных в файловое хранилище из base64.
    Использует upload_delivery_photos для каждого файла.
    Возвращает список URL всех загруженных файлов.
    """
    from api.utils.logging import log_invoice_photos_uploaded, log_invoice_photos_upload_failed, log_message, LogLevel, LogCategory
    
    # Логируем начало процесса
    log_message(
        LogLevel.INFO, 
        LogCategory.FILE_STORAGE, 
        f"Начинаем загрузку фото накладных из base64. object_id: {object_id}, delivery_id: {delivery_id}, файлов: {len(base64_files)}. URL хранилища: {file_storage_client.base_url}"
    )
    
    uploaded_urls = []
    
    for i, base64_data in enumerate(base64_files):
        log_message(
            LogLevel.INFO, 
            LogCategory.FILE_STORAGE, 
            f"Загружаем файл {i+1}/{len(base64_files)} для поставки {delivery_id}"
        )
        
        # Декодируем base64 в байты
        try:
            import base64
            # Убираем префикс data:image/...;base64, если есть
            if ',' in base64_data:
                base64_data = base64_data.split(',', 1)[1]
            # Добавляем padding если необходимо
            missing_padding = len(base64_data) % 4
            if missing_padding:
                base64_data += '=' * (4 - missing_padding)
            file_data = base64.b64decode(base64_data)
            result = file_storage_client.upload_delivery_photos(object_id, delivery_id, [file_data])
            
            if result and result.get('files') and len(result['files']) > 0:
                # Получаем URL из первого файла (может быть url или presigned_url)
                file_info = result['files'][0]
                file_url = file_info.get('url') or file_info.get('presigned_url')
                if file_url:
                    uploaded_urls.append(file_url)
                    log_message(
                        LogLevel.INFO, 
                        LogCategory.FILE_STORAGE, 
                        f"Файл {i+1} успешно загружен для поставки {delivery_id}. URL: {file_url}"
                    )
                else:
                    log_message(
                        LogLevel.ERROR, 
                        LogCategory.FILE_STORAGE, 
                        f"Файл {i+1} загружен для поставки {delivery_id}, но URL не найден. Результат: {result}"
                    )
            else:
                log_message(
                    LogLevel.ERROR, 
                    LogCategory.FILE_STORAGE, 
                    f"Ошибка загрузки файла {i+1} для поставки {delivery_id}. Результат: {result}"
                )
        except Exception as e:
            log_message(
                LogLevel.ERROR, 
                LogCategory.FILE_STORAGE, 
                f"Ошибка декодирования base64 файла {i+1} для поставки {delivery_id}: {str(e)}"
            )
    
    # Логируем итоговый результат
    if uploaded_urls:
        if user_name and user_role:
            log_invoice_photos_uploaded(f"Поставка {delivery_id}", delivery_id, f"{len(uploaded_urls)} файлов", user_name, user_role, len(base64_files))
        
        log_message(
            LogLevel.INFO, 
            LogCategory.FILE_STORAGE, 
            f"Загрузка фото накладных поставки {delivery_id} завершена успешно. Загружено: {len(uploaded_urls)}/{len(base64_files)} файлов. Возвращаем массив из {len(uploaded_urls)} URL"
        )
        return uploaded_urls
    else:
        if user_name and user_role:
            log_invoice_photos_upload_failed(f"Поставка {delivery_id}", delivery_id, "Не удалось загрузить файлы", user_name, user_role, len(base64_files))
        
        log_message(
            LogLevel.ERROR, 
            LogCategory.FILE_STORAGE, 
            f"Загрузка фото накладных поставки {delivery_id} завершилась неудачей. Ни один файл не был загружен из {len(base64_files)} файлов."
        )
        return None


def upload_invoice_photos(files: List[Readable], object_id: int, delivery_id: int, user_name: str = None, user_role: str = None) -> Optional[str]:
    """
    Загружает фото накладных в файловое хранилище.
    Использует upload_delivery_photos для каждого файла.
    """
    from api.utils.logging import log_invoice_photos_uploaded, log_invoice_photos_upload_failed
    
    uploaded_urls = []
    
    for file in files:
        result = file_storage_client.upload_delivery_photos(object_id, delivery_id, [file])
        if result and result.get('url'):
            uploaded_urls.append(result['url'])
    
    # Логируем результат
    if uploaded_urls:
        folder_url = uploaded_urls[0] if len(uploaded_urls) == 1 else f"{len(uploaded_urls)} файлов загружено"
        if user_name and user_role:
            log_invoice_photos_uploaded(delivery_id, folder_url, user_name, user_role, len(files))
        return folder_url
    else:
        if user_name and user_role:
            log_invoice_photos_upload_failed(delivery_id, "Не удалось загрузить файлы", user_name, user_role, len(files))
        return None


def upload_foreman_visit_photos(files: List[Readable], foreman_id: int, user_name: str = None, user_role: str = None) -> Optional[str]:
    """
    Загружает фото визита прораба в файловое хранилище.
    Использует upload_foreman_visit для каждого файла.
    """
    from api.utils.logging import log_file_upload_success, log_file_upload_failed
    
    uploaded_urls = []
    
    for file in files:
        result = file_storage_client.upload_foreman_visit(foreman_id, [file])
        if result and result.get('url'):
            uploaded_urls.append(result['url'])
    
    # Логируем результат
    if uploaded_urls:
        folder_url = uploaded_urls[0] if len(uploaded_urls) == 1 else f"{len(uploaded_urls)} файлов загружено"
        if user_name and user_role:
            log_file_upload_success("фото визита прораба", f"прораб #{foreman_id}", foreman_id, folder_url, user_name, user_role, len(files))
        return folder_url
    else:
        if user_name and user_role:
            log_file_upload_failed("фото визита прораба", f"прораб #{foreman_id}", foreman_id, "Не удалось загрузить файлы", user_name, user_role, len(files))
        return None
