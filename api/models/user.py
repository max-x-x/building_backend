import uuid
from datetime import timedelta
from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

from api.models.timestamp import TimeStampedMixin


class Roles(models.TextChoices):
    ADMIN = "admin", "Администратор"
    SSK = "ssk", "ССК (Служба строительного контроля)"
    IKO = "iko", "ИКО (Инспектор контрольного органа)"
    FOREMAN = "foreman", "Прораб"


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra):
        if not email:
            raise ValueError("Email обязателен")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        if "role" not in extra:
            extra["role"] = Roles.FOREMAN
        return self._create_user(email, password, **extra)

    def create_superuser(self, email, password, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("role", Roles.ADMIN)
        if extra.get("is_staff") is not True:
            raise ValueError("У суперпользователя is_staff=True")
        if extra.get("is_superuser") is not True:
            raise ValueError("У суперпользователя is_superuser=True")
        return self._create_user(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField("ID", primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField("Email", unique=True, db_index=True)
    full_name = models.CharField("ФИО", max_length=200, blank=True)
    phone = models.CharField(
        "Телефон",
        max_length=32,
        blank=True,
        validators=[RegexValidator(r"^[0-9+()\-\s]{6,}$", "Некорректный телефон")],
    )
    role = models.CharField("Роль", max_length=16, choices=Roles.choices, default=Roles.FOREMAN)

    is_active = models.BooleanField("Активен", default=True)
    is_staff = models.BooleanField("Персонал (админка)", default=False)

    date_joined = models.DateTimeField("Дата регистрации", default=timezone.now)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        db_table = "auth_user_custom"
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["-date_joined"]

    def __str__(self):
        return f"{self.email} ({self.role})"


class RefreshToken(TimeStampedMixin):
    """
    Refresh-токены с возможностью ревокации (logout).
    """
    id = models.UUIDField("ID", primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Пользователь",
        on_delete=models.CASCADE,
        related_name="refresh_tokens",
    )
    jti = models.UUIDField("JTI", default=uuid.uuid4, editable=False, db_index=True)
    token = models.TextField("Токен (или хэш)")
    user_agent = models.CharField("User-Agent", max_length=256, blank=True)
    ip = models.GenericIPAddressField("IP", null=True, blank=True)
    expires_at = models.DateTimeField("Истекает")
    revoked = models.BooleanField("Отозван", default=False)

    class Meta:
        verbose_name = "Refresh-токен"
        verbose_name_plural = "Refresh-токены"
        indexes = [models.Index(fields=["user", "revoked", "expires_at"])]

    def __str__(self):
        return f"{self.user.email} / {self.jti} / revoked={self.revoked}"


def _invite_expires_default():
    return timezone.now() + timedelta(days=14)


class Invitation(TimeStampedMixin):
    """
    Инвайт по email под конкретную роль (для онбординга).
    """
    id = models.UUIDField("ID", primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField("Email", db_index=True)
    role = models.CharField("Роль", max_length=16, choices=Roles.choices)
    token = models.UUIDField("Токен-инвайта", default=uuid.uuid4, editable=False, db_index=True)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Пригласил",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    expires_at = models.DateTimeField("Истекает", default=_invite_expires_default)
    accepted_at = models.DateTimeField("Принят", null=True, blank=True)

    class Meta:
        unique_together = ("email", "token")
        verbose_name = "Приглашение"
        verbose_name_plural = "Приглашения"

    def __str__(self):
        return f"{self.email} ({self.role})"

    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at
