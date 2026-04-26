"""
权限装饰器单元测试
覆盖 require_auth, require_roles, require_permissions, require_any_permission
以及 get_user_permissions, get_user_roles 工具函数
"""
import pytest
from unittest.mock import MagicMock
from fastapi import Request
from fastapi.testclient import TestClient

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import app
from middleware.permissions import (
    get_user_permissions,
    get_user_roles,
    require_auth,
    require_roles,
    require_permissions,
    require_any_permission,
)

client = TestClient(app, raise_server_exceptions=False)


class TestGetUserPermissions:
    """测试 get_user_permissions 工具函数"""

    def test_extract_permissions_from_scp(self):
        """从 scp (scope) 字段提取权限"""
        mock_request = MagicMock(spec=Request)
        mock_request.state.token_payload = {
            "sub": "user-123",
            "scp": ["openid", "offline", "read:hotels"],
        }
        perms = get_user_permissions(mock_request)
        assert "openid" in perms
        assert "offline" in perms
        assert "read:hotels" in perms

    def test_extract_permissions_from_scope_string(self):
        """从 scope 字符串提取权限"""
        mock_request = MagicMock(spec=Request)
        mock_request.state.token_payload = {
            "sub": "user-123",
            "scope": "openid offline read:hotels",
        }
        perms = get_user_permissions(mock_request)
        assert "openid" in perms
        assert "offline" in perms
        assert "read:hotels" in perms

    def test_extract_permissions_from_roles(self):
        """从 roles 字段提取权限"""
        mock_request = MagicMock(spec=Request)
        mock_request.state.token_payload = {
            "sub": "user-123",
            "roles": ["admin", "editor"],
        }
        perms = get_user_permissions(mock_request)
        assert "admin" in perms
        assert "editor" in perms

    def test_extract_permissions_from_permissions_field(self):
        """从 permissions 字段提取权限"""
        mock_request = MagicMock(spec=Request)
        mock_request.state.token_payload = {
            "sub": "user-123",
            "permissions": ["write:hotels", "delete:hotels"],
        }
        perms = get_user_permissions(mock_request)
        assert "write:hotels" in perms
        assert "delete:hotels" in perms

    def test_merge_all_permission_sources(self):
        """合并所有权限来源"""
        mock_request = MagicMock(spec=Request)
        mock_request.state.token_payload = {
            "sub": "user-123",
            "scp": ["openid"],
            "roles": ["admin"],
            "permissions": ["write:hotels"],
        }
        perms = get_user_permissions(mock_request)
        assert "openid" in perms
        assert "admin" in perms
        assert "write:hotels" in perms


class TestGetUserRoles:
    """测试 get_user_roles 工具函数"""

    def test_extract_roles_from_list(self):
        """从列表提取角色"""
        mock_request = MagicMock(spec=Request)
        mock_request.state.token_payload = {
            "sub": "user-123",
            "roles": ["admin", "user"],
        }
        roles = get_user_roles(mock_request)
        assert "admin" in roles
        assert "user" in roles

    def test_extract_roles_from_string(self):
        """从字符串提取角色"""
        mock_request = MagicMock(spec=Request)
        mock_request.state.token_payload = {
            "sub": "user-123",
            "roles": "admin",
        }
        roles = get_user_roles(mock_request)
        assert "admin" in roles

    def test_empty_roles(self):
        """空角色列表"""
        mock_request = MagicMock(spec=Request)
        mock_request.state.token_payload = {
            "sub": "user-123",
            "roles": [],
        }
        roles = get_user_roles(mock_request)
        assert len(roles) == 0


class TestRequireAuth:
    """测试 require_auth 装饰器"""

    def test_unauthenticated_request_returns_401(self):
        """未认证用户访问被拒绝，返回 401"""
        # 创建没有 user_id 的 request state
        mock_request = MagicMock(spec=Request)
        mock_state = MagicMock()
        mock_state.user_id = None  # 明确设置为 None
        mock_request.state = mock_state

        @require_auth
        async def protected_endpoint(request: Request):
            return {"success": True}

        import asyncio
        result = asyncio.run(protected_endpoint(mock_request))
        assert result.status_code == 401

    def test_authenticated_request_passes(self):
        """已认证用户可以正常访问"""
        # 这个测试验证装饰器不阻止已认证请求
        # 由于装饰器需要从参数中查找 Request，实际测试通过集成测试进行
        mock_request = MagicMock(spec=Request)
        mock_request.state.user_id = "user-123"
        mock_request.state.token_payload = {"sub": "user-123"}

        @require_auth
        async def protected_endpoint(request: Request):
            return {"success": True, "user_id": request.state.user_id}

        import asyncio
        result = asyncio.run(protected_endpoint(mock_request))
        # 如果没有抛出异常或返回错误响应，说明装饰器允许通过
        assert not hasattr(result, 'status_code') or result.status_code != 401


class TestRequireRoles:
    """测试 require_roles 装饰器"""

    def test_user_has_required_role(self):
        """用户有所需角色，允许访问"""
        mock_request = MagicMock(spec=Request)
        mock_request.state.user_id = "user-123"
        mock_request.state.token_payload = {"sub": "user-123", "roles": ["admin", "user"]}

        @require_roles("admin")
        async def admin_endpoint(request: Request):
            return {"success": True}

        import asyncio
        result = asyncio.run(admin_endpoint(mock_request))
        # 如果用户有 admin 角色，不应返回 403
        assert not hasattr(result, 'status_code') or result.status_code != 403

    def test_user_missing_required_role(self):
        """用户没有所需角色，返回 403"""
        mock_request = MagicMock(spec=Request)
        mock_request.state.user_id = "user-123"
        mock_request.state.token_payload = {"sub": "user-123", "roles": ["user"]}

        @require_roles("admin")
        async def admin_endpoint(request: Request):
            return {"success": True}

        import asyncio
        result = asyncio.run(admin_endpoint(mock_request))
        assert result.status_code == 403
        assert "ROLE_REQUIRED" in result.body.decode()

    def test_user_has_any_of_required_roles(self):
        """用户有任一所需角色（多选一），允许访问"""
        mock_request = MagicMock(spec=Request)
        mock_request.state.user_id = "user-123"
        mock_request.state.token_payload = {"sub": "user-123", "roles": ["superuser"]}

        @require_roles("admin", "superuser")
        async def elevated_endpoint(request: Request):
            return {"success": True}

        import asyncio
        result = asyncio.run(elevated_endpoint(mock_request))
        assert not hasattr(result, 'status_code') or result.status_code != 403


class TestRequirePermissions:
    """测试 require_permissions 装饰器"""

    def test_user_has_all_required_permissions(self):
        """用户有所需权限（全部），允许访问"""
        mock_request = MagicMock(spec=Request)
        mock_request.state.user_id = "user-123"
        mock_request.state.token_payload = {
            "sub": "user-123",
            "permissions": ["read:hotels", "write:hotels"],
        }

        @require_permissions("read:hotels", "write:hotels")
        async def data_endpoint(request: Request):
            return {"success": True}

        import asyncio
        result = asyncio.run(data_endpoint(mock_request))
        assert not hasattr(result, 'status_code') or result.status_code != 403

    def test_user_missing_some_permissions(self):
        """用户缺少部分权限，返回 403"""
        mock_request = MagicMock(spec=Request)
        mock_request.state.user_id = "user-123"
        mock_request.state.token_payload = {
            "sub": "user-123",
            "permissions": ["read:hotels"],
        }

        @require_permissions("read:hotels", "write:hotels")
        async def data_endpoint(request: Request):
            return {"success": True}

        import asyncio
        result = asyncio.run(data_endpoint(mock_request))
        assert result.status_code == 403
        assert "PERMISSION_DENIED" in result.body.decode()


class TestRequireAnyPermission:
    """测试 require_any_permission 装饰器"""

    def test_user_has_one_required_permission(self):
        """用户有任一所需权限，允许访问"""
        mock_request = MagicMock(spec=Request)
        mock_request.state.user_id = "user-123"
        mock_request.state.token_payload = {
            "sub": "user-123",
            "permissions": ["read:hotels"],
        }

        @require_any_permission("read:hotels", "admin:read")
        async def data_endpoint(request: Request):
            return {"success": True}

        import asyncio
        result = asyncio.run(data_endpoint(mock_request))
        assert not hasattr(result, 'status_code') or result.status_code != 403

    def test_user_has_no_required_permissions(self):
        """用户没有任何所需权限，返回 403"""
        mock_request = MagicMock(spec=Request)
        mock_request.state.user_id = "user-123"
        mock_request.state.token_payload = {
            "sub": "user-123",
            "permissions": ["read:users"],
        }

        @require_any_permission("read:hotels", "admin:read")
        async def data_endpoint(request: Request):
            return {"success": True}

        import asyncio
        result = asyncio.run(data_endpoint(mock_request))
        assert result.status_code == 403
        assert "PERMISSION_DENIED" in result.body.decode()
