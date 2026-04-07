"""权限校验模块测试."""

import pytest
from fastapi import HTTPException

from auth.dependencies import parse_user_permissions, require_permission, require_role
from auth.models import UserPermissions, UserRole


class TestUserPermissions:
    """测试用户权限模型."""

    def test_global_manager_has_all_permissions(self):
        user = UserPermissions(
            user_id="u1",
            role=UserRole.GLOBAL_MANAGER,
            permissions=[],
        )
        assert user.has_permission("any_permission") is True
        assert user.can_export() is True
        assert user.can_submit_conclusion() is True

    def test_business_user_needs_explicit_permission(self):
        user = UserPermissions(
            user_id="u2",
            role=UserRole.BUSINESS_USER,
            permissions=["submit_conclusions"],
        )
        assert user.has_permission("submit_conclusions") is True
        assert user.can_submit_conclusion() is True
        assert user.can_export() is False

    def test_regional_manager_can_submit(self):
        user = UserPermissions(
            user_id="u3",
            role=UserRole.REGIONAL_MANAGER,
            permissions=[],
        )
        assert user.can_submit_conclusion() is True
        assert user.can_export() is False


class TestParseUserPermissions:
    """测试请求头解析."""

    def test_parse_with_headers(self):
        user = parse_user_permissions(
            x_user_id="u1",
            x_user_role="global_manager",
            x_assigned_regions="asia_pacific,singapore",
            x_permissions="view_all,export_reports",
        )
        assert user.user_id == "u1"
        assert user.role == UserRole.GLOBAL_MANAGER
        assert user.assigned_regions == ["asia_pacific", "singapore"]
        assert user.permissions == ["view_all", "export_reports"]

    def test_parse_with_defaults(self):
        user = parse_user_permissions()
        assert user.user_id == "anonymous"
        assert user.role == UserRole.BUSINESS_USER
        assert user.assigned_regions == []
        assert user.permissions == []

    def test_parse_invalid_role_defaults_to_business(self):
        user = parse_user_permissions(x_user_role="unknown_role")
        assert user.role == UserRole.BUSINESS_USER


class TestRequireRole:
    """测试角色校验依赖."""

    def test_allow_matching_role(self):
        user = UserPermissions(user_id="u1", role=UserRole.GLOBAL_MANAGER)
        dep = require_role(UserRole.GLOBAL_MANAGER)
        assert dep(user=user) == user

    def test_reject_non_matching_role(self):
        user = UserPermissions(user_id="u1", role=UserRole.BUSINESS_USER)
        dep = require_role(UserRole.GLOBAL_MANAGER)
        with pytest.raises(HTTPException) as exc_info:
            dep(user=user)
        assert exc_info.value.status_code == 403


class TestRequirePermission:
    """测试权限校验依赖."""

    def test_allow_matching_permission(self):
        user = UserPermissions(
            user_id="u1",
            role=UserRole.BUSINESS_USER,
            permissions=["export_reports"],
        )
        dep = require_permission("export_reports")
        assert dep(user=user) == user

    def test_reject_missing_permission(self):
        user = UserPermissions(
            user_id="u1",
            role=UserRole.BUSINESS_USER,
            permissions=[],
        )
        dep = require_permission("export_reports")
        with pytest.raises(HTTPException) as exc_info:
            dep(user=user)
        assert exc_info.value.status_code == 403
