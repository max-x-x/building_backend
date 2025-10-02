import base64
import mimetypes
from typing import List, Dict, Optional, Union
from datetime import date as dt_date

import requests
from django.conf import settings

from api.utils.logging import (
    log_file_storage_connection_failed,
    log_file_storage_timeout,
    log_file_storage_response_error,
)


Readable = Union[bytes, str, "io.BytesIO", "django.core.files.uploadedfile.InMemoryUploadedFile", "django.core.files.uploadedfile.TemporaryUploadedFile"]  # noqa: F821


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
    def _read_bytes(file: Readable) -> (bytes, Optional[str], Optional[str]):
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
