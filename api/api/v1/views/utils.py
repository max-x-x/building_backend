from rest_framework.permissions import BasePermission
import requests
from django.conf import settings

class RoleRequired(BasePermission):
    """
    Пример: permission_classes = [RoleRequired.as_permitted("admin")]
    """
    allowed_roles: tuple[str, ...] = ()

    @classmethod
    def as_permitted(cls, *roles):
        class _P(cls):
            allowed_roles = roles
        return _P

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if not self.allowed_roles:
            return True
        return request.user.role in self.allowed_roles


def send_notification(user_id: int | None, email: str | None, subject: str, message: str) -> None:
    """
    Отправка уведомления во внешний сервис. Ошибки не падают наружу.
    """
    url = getattr(settings, "NOTIFY_SERVICE_URL", "")
    if not url:
        return
    try:
        payload = {
            "user_id": user_id,
            "email": email,
            "subject": subject,
            "message": message,
        }
        requests.post(url, json=payload, timeout=5)
    except Exception:
        # гасим сбои внешнего сервиса, чтобы не ломать основной флоу
        pass