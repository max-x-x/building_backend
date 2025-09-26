from django.contrib import admin

from api.forms.user import UserCreationForm, UserChangeForm
from api.models.user import User, RefreshToken, Invitation
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form = UserCreationForm          # форма создания (с паролями)
    form = UserChangeForm               # форма изменения (показывает хэш)
    model = User

    list_display = ("email", "full_name", "role", "is_active", "is_staff", "date_joined")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("email", "full_name", "phone")
    ordering = ("-date_joined",)
    filter_horizontal = ("groups", "user_permissions")

    fieldsets = (
        ("Личные данные", {"fields": ("email", "full_name", "phone", "role", "password")}),
        ("Права доступа", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Даты", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "full_name", "phone", "role", "password1", "password2", "is_staff", "is_superuser"),
        }),
    )
    readonly_fields = ("date_joined", "last_login")

@admin.register(RefreshToken)
class RefreshTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "jti", "revoked", "created_at", "expires_at", "ip", "user_agent")
    list_filter = ("revoked",)
    search_fields = ("user__email", "jti")


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ("email", "role", "token", "created_at", "expires_at", "accepted_at", "invited_by")
    list_filter = ("role",)
    search_fields = ("email", "token")
