from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils import timezone

from api.forms.user import UserCreationForm, UserChangeForm
from api.models.user import User, RefreshToken, Invitation, Roles
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form = UserCreationForm          # форма создания (с паролями)
    form = UserChangeForm               # форма изменения (показывает хэш)
    model = User

    list_display = ("email", "full_name", "role_badge", "phone", "is_active", "is_staff", "date_joined")
    list_filter = ("role", "is_active", "is_staff", "date_joined")
    search_fields = ("email", "full_name", "phone")
    ordering = ("-date_joined",)
    filter_horizontal = ("groups", "user_permissions")
    list_per_page = 25

    fieldsets = (
        ("👤 Личные данные", {
            "fields": ("email", "full_name", "phone", "role", "password"),
            "classes": ("wide",)
        }),
        ("🔐 Права доступа", {
            "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
            "classes": ("collapse",)
        }),
        ("📅 Даты", {
            "fields": ("last_login", "date_joined"),
            "classes": ("collapse",)
        }),
    )
    add_fieldsets = (
        ("👤 Создание пользователя", {
            "classes": ("wide",),
            "fields": ("email", "full_name", "phone", "role", "password1", "password2", "is_staff", "is_superuser"),
        }),
    )
    readonly_fields = ("date_joined", "last_login")

    def role_badge(self, obj):
        """Отображает роль с цветным бейджем."""
        colors = {
            Roles.ADMIN: "#dc3545",      # красный
            Roles.SSK: "#007bff",        # синий  
            Roles.IKO: "#28a745",       # зеленый
            Roles.FOREMAN: "#ffc107",    # желтый
        }
        color = colors.get(obj.role, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_role_display()
        )
    role_badge.short_description = "Роль"
    role_badge.admin_order_field = "role"

@admin.register(RefreshToken)
class RefreshTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "jti_short", "revoked_badge", "created_at", "expires_at", "ip")
    list_filter = ("revoked", "created_at")
    search_fields = ("user__email", "jti", "ip")
    readonly_fields = ("jti", "created_at", "expires_at")
    list_per_page = 25

    def jti_short(self, obj):
        """Сокращенный JTI."""
        jti_str = str(obj.jti)
        return f"{jti_str[:8]}..."
    jti_short.short_description = "JTI"

    def revoked_badge(self, obj):
        """Статус отзыва токена."""
        if obj.revoked:
            return format_html('<span style="color: #dc3545;">❌ Отозван</span>')
        return format_html('<span style="color: #28a745;">✅ Активен</span>')
    revoked_badge.short_description = "Статус"


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ("email", "role_badge", "status_badge", "created_at", "expires_at", "invited_by")
    list_filter = ("role", "created_at")
    search_fields = ("email", "token")
    readonly_fields = ("token", "created_at", "expires_at")
    list_per_page = 25

    def role_badge(self, obj):
        """Отображает роль с цветным бейджем."""
        colors = {
            Roles.ADMIN: "#dc3545",
            Roles.SSK: "#007bff", 
            Roles.IKO: "#28a745",
            Roles.FOREMAN: "#ffc107",
        }
        color = colors.get(obj.role, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            color, obj.get_role_display()
        )
    role_badge.short_description = "Роль"

    def status_badge(self, obj):
        """Статус приглашения."""
        if obj.accepted_at:
            return format_html('<span style="color: #28a745;">✅ Принято</span>')
        elif obj.expires_at and obj.expires_at < timezone.now():
            return format_html('<span style="color: #dc3545;">⏰ Истекло</span>')
        else:
            return format_html('<span style="color: #ffc107;">⏳ Ожидает</span>')
    status_badge.short_description = "Статус"
