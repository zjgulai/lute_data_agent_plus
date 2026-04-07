"""权限校验依赖函数."""

from typing import Optional

from fastapi import Depends, Header, HTTPException

from .models import UserPermissions, UserRole


def parse_user_permissions(
    x_user_id: Optional[str] = Header(None),
    x_user_role: Optional[str] = Header(None),
    x_assigned_regions: Optional[str] = Header(None),
    x_permissions: Optional[str] = Header(None),
) -> UserPermissions:
    """从请求头解析用户权限信息.

    如果请求头缺失，默认降级为 business_user 角色（最小权限原则）。
    """
    # 确保值为字符串或 None（兼容直接调用测试）
    user_id_str = x_user_id if isinstance(x_user_id, str) else None
    role_str = x_user_role if isinstance(x_user_role, str) else None
    regions_str = x_assigned_regions if isinstance(x_assigned_regions, str) else None
    perms_str = x_permissions if isinstance(x_permissions, str) else None

    role = role_str or "business_user"
    try:
        user_role = UserRole(role)
    except ValueError:
        user_role = UserRole.BUSINESS_USER

    return UserPermissions(
        user_id=user_id_str or "anonymous",
        role=user_role,
        assigned_regions=regions_str.split(",") if regions_str else [],
        permissions=perms_str.split(",") if perms_str else [],
    )


def require_role(*roles: UserRole):
    """要求指定角色的依赖工厂."""
    def checker(
        user: UserPermissions = Depends(parse_user_permissions),
    ) -> UserPermissions:
        if not user.has_role(*roles):
            raise HTTPException(
                status_code=403,
                detail=f"需要角色: {', '.join(r.value for r in roles)}",
            )
        return user
    return checker


def require_permission(permission: str):
    """要求指定权限的依赖工厂."""
    def checker(
        user: UserPermissions = Depends(parse_user_permissions),
    ) -> UserPermissions:
        if not user.has_permission(permission):
            raise HTTPException(
                status_code=403,
                detail=f"需要权限: {permission}",
            )
        return user
    return checker
