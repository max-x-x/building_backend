import jwt
import uuid
from datetime import datetime, timedelta, timezone as pytimezone

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework import exceptions

from api.models.user import RefreshToken

User = get_user_model()


def _now_utc() -> datetime:
    return datetime.now(tz=pytimezone.utc)


def create_access_token(user) -> str:
    ttl = int(getattr(settings, "JWT_ACCESS_TTL_MIN", 15))
    payload = {
        "sub": str(user.id),
        "role": user.role,
        "type": "access",
        "exp": _now_utc() + timedelta(minutes=ttl),
        "iat": _now_utc(),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user, user_agent: str | None = None, ip: str | None = None) -> tuple[str, RefreshToken]:
    ttl_days = int(getattr(settings, "JWT_REFRESH_TTL_DAYS", 30))
    jti = uuid.uuid4()
    payload = {
        "sub": str(user.id),
        "role": user.role,
        "type": "refresh",
        "jti": str(jti),
        "exp": _now_utc() + timedelta(days=ttl_days),
        "iat": _now_utc(),
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    rt = RefreshToken.objects.create(
        user=user,
        jti=jti,
        token=token,
        user_agent=(user_agent or "")[:256],
        ip=ip,
        expires_at=timezone.now() + timedelta(days=ttl_days),
    )
    return token, rt


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise exceptions.AuthenticationFailed("Token expired")
    except jwt.InvalidTokenError:
        raise exceptions.AuthenticationFailed("Invalid token")


class JWTAuthentication(BaseAuthentication):
    keyword = b"Bearer"

    def authenticate(self, request):
        auth = get_authorization_header(request).split()
        if not auth or auth[0].lower() != self.keyword.lower():
            return None
        if len(auth) == 1:
            raise exceptions.AuthenticationFailed("Invalid auth header")
        if len(auth) > 2:
            raise exceptions.AuthenticationFailed("Invalid auth header")

        token = auth[1].decode("utf-8")
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise exceptions.AuthenticationFailed("Access token required")

        user_id = payload.get("sub")
        try:
            user = User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed("User not found")
        return (user, None)


