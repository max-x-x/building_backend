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


def send_notification(user_id: str | None, email: str | None, subject: str, message: str, sender_name: str = None, sender_role: str = None) -> None:
    """
    Отправка уведомления во внешний сервис. Ошибки не падают наружу.
    """
    from api.utils.logging import log_notification_sent, log_notification_failed
    
    url = getattr(settings, "NOTIFY_SERVICE_URL", "")
    print(url)
    if not url:
        # Логируем что URL не настроен
        if sender_name and sender_role:
            log_notification_failed(email, subject, "NOTIFY_SERVICE_URL не настроен", sender_name, sender_role)
        return
    try:
        payload = {
            "user_id": str(user_id) if user_id else None,
            "email": email,
            "subject": subject,
            "message": message,
        }
        print(payload)
        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()
        
        # Логируем успешную отправку в БД
        if sender_name and sender_role:
            log_notification_sent(email, email, subject, sender_name, sender_role)
            
    except Exception as e:
        print(f"Failed to send notification to {email}: {subject}: {message}")
        # Логируем ошибку отправки в БД
        if sender_name and sender_role:
            log_notification_failed(email, subject, str(e), sender_name, sender_role)
        pass