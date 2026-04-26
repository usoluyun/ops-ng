"""
Strapi 客户端
用于与 Strapi 用户管理 API 交互
"""
import os
from typing import Optional

import httpx

STRAPI_URL = os.getenv("STRAPI_URL", "http://localhost:1337")


async def verify_credentials(identifier: str, password: str) -> Optional[dict]:
    """
    调用 Strapi /api/auth/local 验证用户凭证。

    Args:
        identifier: 用户名或邮箱
        password: 明文密码

    Returns:
        用户信息 dict，验证失败返回 None
    """
    async with httpx.AsyncClient(base_url=STRAPI_URL, timeout=10.0) as client:
        try:
            resp = await client.post(
                "/api/auth/local",
                json={"identifier": identifier, "password": password},
            )
        except httpx.RequestError:
            return None

    if resp.status_code == 200:
        data = resp.json()
        return {
            "id": str(data["user"]["id"]),
            "email": data["user"]["email"],
            "username": data["user"].get("username", identifier),
            "jwt": data.get("jwt"),
        }
    return None


async def get_user_by_id(user_id: str) -> Optional[dict]:
    """
    根据 ID 获取用户信息

    Args:
        user_id: 用户 ID

    Returns:
        用户信息 dict，不存在返回 None
    """
    async with httpx.AsyncClient(base_url=STRAPI_URL, timeout=10.0) as client:
        try:
            resp = await client.get(f"/api/users/{user_id}")
        except httpx.RequestError:
            return None

    if resp.status_code == 200:
        return resp.json()
    return None


async def create_user(
    email: str,
    password: str,
    username: str,
    role: str = "authenticated",
) -> Optional[dict]:
    """
    创建新用户

    Args:
        email: 邮箱
        password: 明文密码
        username: 用户名
        role: 角色，默认 authenticated

    Returns:
        创建的用户信息 dict，失败返回 None
    """
    async with httpx.AsyncClient(base_url=STRAPI_URL, timeout=10.0) as client:
        try:
            resp = await client.post(
                "/api/auth/register",
                json={
                    "email": email,
                    "password": password,
                    "username": username,
                },
            )
        except httpx.RequestError:
            return None

    if resp.status_code in (200, 201):
        data = resp.json()
        return {
            "id": str(data["user"]["id"]),
            "email": data["user"]["email"],
            "username": data["user"].get("username", username),
            "jwt": data.get("jwt"),
        }
    return None


async def check_email_exists(email: str) -> bool:
    """
    检查邮箱是否已注册

    Args:
        email: 邮箱地址

    Returns:
        True if exists, False otherwise
    """
    async with httpx.AsyncClient(base_url=STRAPI_URL, timeout=10.0) as client:
        try:
            resp = await client.get(
                "/api/users",
                params={"filters[email][$eq]": email},
            )
        except httpx.RequestError:
            return False

    if resp.status_code == 200:
        data = resp.json()
        return len(data) > 0
    return False
