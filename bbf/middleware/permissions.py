"""
用户权限装饰器
提供基于角色和权限的访问控制
"""
from functools import wraps
from typing import Callable, List, Optional, Set

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse


class PermissionDenied(Exception):
    """权限不足异常"""

    def __init__(self, message: str = "Permission denied", required_permissions: Optional[List[str]] = None):
        self.message = message
        self.required_permissions = required_permissions or []
        super().__init__(self.message)


def get_user_permissions(request: Request) -> Set[str]:
    """
    从 request.state.token_payload 中提取用户权限

    Args:
        request: FastAPI 请求对象

    Returns:
        用户权限集合
    """
    payload = getattr(request.state, "token_payload", {})

    # 从 token 中提取权限信息
    # Hydra 的 scope 字段包含权限信息
    scopes = payload.get("scp", []) or payload.get("scope", "").split()
    roles = payload.get("roles", [])
    permissions = payload.get("permissions", [])

    # 合并所有权限
    all_permissions: Set[str] = set()
    all_permissions.update(scopes)
    all_permissions.update(roles)
    all_permissions.update(permissions)

    return all_permissions


def get_user_roles(request: Request) -> Set[str]:
    """
    从 request.state.token_payload 中提取用户角色

    Args:
        request: FastAPI 请求对象

    Returns:
        用户角色集合
    """
    payload = getattr(request.state, "token_payload", {})

    roles = payload.get("roles", [])
    if isinstance(roles, str):
        roles = [roles]

    return set(roles)


def require_auth(func: Callable) -> Callable:
    """
    要求用户已认证的装饰器

    Usage:
        @router.get("/protected")
        @require_auth
        async def protected_endpoint(request: Request):
            user_id = request.state.user_id
            ...
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        # 查找 request 参数
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break

        if request is None:
            request = kwargs.get("request")

        if request is None:
            return JSONResponse(
                status_code=401,
                content={"error": "Authentication required", "code": "AUTH_REQUIRED"},
            )

        # 检查是否有用户信息
        user_id = getattr(request.state, "user_id", None)
        if not user_id:
            return JSONResponse(
                status_code=401,
                content={"error": "Authentication required", "code": "AUTH_REQUIRED"},
            )

        return await func(*args, **kwargs)

    return wrapper


def require_roles(*required_roles: str):
    """
    要求用户具有指定角色的装饰器

    Usage:
        @router.get("/admin")
        @require_roles("admin", "superuser")
        async def admin_endpoint(request: Request):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if request is None:
                request = kwargs.get("request")

            if request is None:
                return JSONResponse(
                    status_code=401,
                    content={"error": "Authentication required", "code": "AUTH_REQUIRED"},
                )

            user_roles = get_user_roles(request)
            if not any(role in user_roles for role in required_roles):
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": f"Requires one of roles: {', '.join(required_roles)}",
                        "code": "ROLE_REQUIRED",
                    },
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_permissions(*required_permissions: str):
    """
    要求用户具有指定权限的装饰器

    Usage:
        @router.get("/data")
        @require_permissions("read:data", "write:data")
        async def data_endpoint(request: Request):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if request is None:
                request = kwargs.get("request")

            if request is None:
                return JSONResponse(
                    status_code=401,
                    content={"error": "Authentication required", "code": "AUTH_REQUIRED"},
                )

            user_permissions = get_user_permissions(request)

            # 检查是否有所需的权限（需要全部满足）
            missing_permissions = [p for p in required_permissions if p not in user_permissions]
            if missing_permissions:
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": f"Missing permissions: {', '.join(missing_permissions)}",
                        "code": "PERMISSION_DENIED",
                    },
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_any_permission(*required_permissions: str):
    """
    要求用户具有任一指定权限的装饰器（OR 逻辑）

    Usage:
        @router.get("/data")
        @require_any_permission("read:data", "admin:read")
        async def data_endpoint(request: Request):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if request is None:
                request = kwargs.get("request")

            if request is None:
                return JSONResponse(
                    status_code=401,
                    content={"error": "Authentication required", "code": "AUTH_REQUIRED"},
                )

            user_permissions = get_user_permissions(request)

            # 检查是否有任一所需权限
            if not any(p in user_permissions for p in required_permissions):
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": f"Requires one of permissions: {', '.join(required_permissions)}",
                        "code": "PERMISSION_DENIED",
                    },
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator
