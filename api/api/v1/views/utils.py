from rest_framework.permissions import BasePermission

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