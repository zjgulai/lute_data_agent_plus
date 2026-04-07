"""权限认证模块."""

from .dependencies import require_permission, require_role
from .models import UserPermissions, UserRole

__all__ = [
    "require_permission",
    "require_role",
    "UserPermissions",
    "UserRole",
]
