"""
Hydra 客户端
用于与 ORY Hydra OAuth2 API 交互
"""
import os
from typing import List

import httpx

HYDRA_ADMIN_URL = os.getenv("HYDRA_ADMIN_URL", "http://localhost:4445")


async def get_login_request(challenge: str) -> dict:
    """
    获取登录请求信息

    Args:
        challenge: login_challenge

    Returns:
        登录请求信息 dict

    Raises:
        httpx.HTTPStatusError: 请求失败
    """
    async with httpx.AsyncClient(base_url=HYDRA_ADMIN_URL, timeout=10.0) as client:
        resp = await client.get(
            f"/admin/oauth2/auth/requests/login",
            params={"login_challenge": challenge},
        )
        resp.raise_for_status()
        return resp.json()


async def accept_login(challenge: str, subject: str, remember: bool = False) -> str:
    """
    接受登录请求，返回 Hydra 要求的 redirect_to URL

    Args:
        challenge: login_challenge
        subject: 用户 ID (sub)
        remember: 是否记住用户

    Returns:
        redirect_to URL

    Raises:
        httpx.HTTPStatusError: 请求失败
    """
    async with httpx.AsyncClient(base_url=HYDRA_ADMIN_URL, timeout=10.0) as client:
        resp = await client.put(
            f"/admin/oauth2/auth/requests/login/accept",
            params={"login_challenge": challenge},
            json={
                "subject": subject,
                "remember": remember,
                "remember_for": 0,
            },
        )
        resp.raise_for_status()
        return resp.json()["redirect_to"]


async def get_consent_request(challenge: str) -> dict:
    """
    获取 Consent 请求信息

    Args:
        challenge: consent_challenge

    Returns:
        Consent 请求信息 dict

    Raises:
        httpx.HTTPStatusError: 请求失败
    """
    async with httpx.AsyncClient(base_url=HYDRA_ADMIN_URL, timeout=10.0) as client:
        resp = await client.get(
            f"/admin/oauth2/auth/requests/consent",
            params={"consent_challenge": challenge},
        )
        resp.raise_for_status()
        return resp.json()


async def accept_consent(
    challenge: str,
    subject: str,
    requested_scope: List[str],
) -> str:
    """
    自动接受 Consent，返回 redirect_to URL

    Args:
        challenge: consent_challenge
        subject: 用户 ID (sub)
        requested_scope: 请求的权限范围

    Returns:
        redirect_to URL

    Raises:
        httpx.HTTPStatusError: 请求失败
    """
    async with httpx.AsyncClient(base_url=HYDRA_ADMIN_URL, timeout=10.0) as client:
        resp = await client.put(
            f"/admin/oauth2/auth/requests/consent/accept",
            params={"consent_challenge": challenge},
            json={
                "grant_scope": requested_scope,
                "grant_access_token_audience": [],
                "session": {
                    "access_token": {"sub": subject},
                    "id_token": {"sub": subject},
                },
            },
        )
        resp.raise_for_status()
        return resp.json()["redirect_to"]


async def reject_login(challenge: str, error: str, error_description: str) -> str:
    """
    拒绝登录请求

    Args:
        challenge: login_challenge
        error: 错误码
        error_description: 错误描述

    Returns:
        redirect_to URL

    Raises:
        httpx.HTTPStatusError: 请求失败
    """
    async with httpx.AsyncClient(base_url=HYDRA_ADMIN_URL, timeout=10.0) as client:
        resp = await client.put(
            f"/admin/oauth2/auth/requests/login/reject",
            params={"login_challenge": challenge},
            json={
                "error": error,
                "error_description": error_description,
            },
        )
        resp.raise_for_status()
        return resp.json()["redirect_to"]


async def reject_consent(challenge: str, error: str, error_description: str) -> str:
    """
    拒绝 Consent 请求

    Args:
        challenge: consent_challenge
        error: 错误码
        error_description: 错误描述

    Returns:
        redirect_to URL

    Raises:
        httpx.HTTPStatusError: 请求失败
    """
    async with httpx.AsyncClient(base_url=HYDRA_ADMIN_URL, timeout=10.0) as client:
        resp = await client.put(
            f"/admin/oauth2/auth/requests/consent/reject",
            params={"consent_challenge": challenge},
            json={
                "error": error,
                "error_description": error_description,
            },
        )
        resp.raise_for_status()
        return resp.json()["redirect_to"]
