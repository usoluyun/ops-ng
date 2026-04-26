"""
用户 API 路由
提供用户信息、权限等接口
"""
from typing import Optional

from fastapi import APIRouter, Request, Query
from fastapi.responses import JSONResponse

from middleware.permissions import get_user_permissions, get_user_roles, require_auth

router = APIRouter(tags=["users"])


@router.get("/users/me")
async def get_current_user(request: Request):
    """
    获取当前登录用户信息

    Returns:
        用户 ID、角色、权限等信息
    """
    user_id = getattr(request.state, "user_id", None)
    token_payload = getattr(request.state, "token_payload", {})

    if not user_id:
        return JSONResponse(
            status_code=401,
            content={"error": "Not authenticated", "code": "AUTH_REQUIRED"},
        )

    return {
        "id": user_id,
        "username": token_payload.get("username", ""),
        "email": token_payload.get("email", ""),
        "roles": list(get_user_roles(request)),
        "permissions": list(get_user_permissions(request)),
        "token_expiry": getattr(request.state, "token_expiry", None),
    }


@router.get("/users/me/permissions")
async def get_current_user_permissions(request: Request):
    """
    获取当前用户的权限列表

    Returns:
        权限集合
    """
    if not getattr(request.state, "user_id", None):
        return JSONResponse(
            status_code=401,
            content={"error": "Not authenticated", "code": "AUTH_REQUIRED"},
        )

    permissions = get_user_permissions(request)
    return {
        "permissions": list(permissions),
    }


@router.get("/users/me/roles")
async def get_current_user_roles(request: Request):
    """
    获取当前用户的角色列表

    Returns:
        角色集合
    """
    if not getattr(request.state, "user_id", None):
        return JSONResponse(
            status_code=401,
            content={"error": "Not authenticated", "code": "AUTH_REQUIRED"},
        )

    roles = get_user_roles(request)
    return {
        "roles": list(roles),
    }


@router.get("/users/{user_id}")
async def get_user_by_id(user_id: str, request: Request):
    """
    根据 ID 获取用户信息

    注意：此接口需要管理员权限
    """
    # TODO: 实现通过 Strapi API 获取用户信息
    # 目前只是占位符
    return {
        "id": user_id,
        "message": "User info lookup via Strapi API not implemented yet",
    }


@router.get("/users")
async def list_users(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
):
    """
    获取用户列表

    注意：此接口需要管理员权限
    """
    # TODO: 实现通过 Strapi API 获取用户列表
    # 目前只是占位符
    return {
        "data": [],
        "meta": {
            "pagination": {
                "page": page,
                "pageSize": page_size,
                "total": 0,
            }
        },
        "message": "User list via Strapi API not implemented yet",
    }
