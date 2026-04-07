"""权限模型定义."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class UserRole(str, Enum):
    """用户角色枚举."""

    GLOBAL_MANAGER = "global_manager"
    REGIONAL_MANAGER = "regional_manager"
    BUSINESS_USER = "business_user"


class UserPermissions(BaseModel):
    """用户权限信息.

    从请求头中解析的用户权限上下文。
    """

    user_id: str = Field(..., description="用户ID")
    role: UserRole = Field(..., description="用户角色")
    assigned_regions: list[str] = Field(default_factory=list, description="负责区域")
    permissions: list[str] = Field(default_factory=list, description="权限列表")

    def has_permission(self, permission: str) -> bool:
        """检查是否拥有指定权限."""
        if self.role == UserRole.GLOBAL_MANAGER:
            return True
        return permission in self.permissions

    def has_role(self, *roles: UserRole) -> bool:
        """检查是否属于指定角色之一."""
        return self.role in roles

    def can_export(self) -> bool:
        """检查是否有导出权限."""
        return self.has_permission("export_reports")

    def can_submit_conclusion(self) -> bool:
        """检查是否有提交结论权限."""
        if self.role in (UserRole.GLOBAL_MANAGER, UserRole.REGIONAL_MANAGER):
            return True
        return self.has_permission("submit_conclusions")
