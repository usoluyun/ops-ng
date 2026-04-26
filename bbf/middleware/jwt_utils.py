"""
JWT 工具类
基于 ORY Hydra JWKS 端点实现 JWT 验证
"""
import os
import time
from typing import Optional

import httpx
import jwt
from jwt import PyJWKClient, PyJWKClientError

HYDRA_PUBLIC_URL = os.getenv("HYDRA_PUBLIC_URL", "http://localhost:4444")
JWKS_URI = f"{HYDRA_PUBLIC_URL}/.well-known/jwks.json"

# JWKS 缓存
_jwks_client: Optional[PyJWKClient] = None
_jwks_cache_time: float = 0
JWKS_CACHE_TTL = 3600  # 1 hour


def get_jwks_client() -> PyJWKClient:
    """获取 JWKS 客户端，支持缓存"""
    global _jwks_client, _jwks_cache_time
    now = time.time()
    if _jwks_client is None or (now - _jwks_cache_time) > JWKS_CACHE_TTL:
        _jwks_client = PyJWKClient(JWKS_URI)
        _jwks_cache_time = now
    return _jwks_client


def verify_token(token: str) -> dict:
    """
    验证 JWT Token

    Args:
        token: JWT token 字符串

    Returns:
        解码后的 payload

    Raises:
        jwt.ExpiredSignatureError: Token 已过期
        jwt.InvalidTokenError: Token 无效
        PyJWKClientError: JWKS 获取失败
    """
    jwks_client = get_jwks_client()
    signing_key = jwks_client.get_signing_key_from_jwt(token)
    payload = jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        options={"verify_aud": False},
    )
    return payload


def decode_token_without_verify(token: str) -> dict:
    """
    解码 Token 但不验证签名（用于提取基本信息）

    Args:
        token: JWT token 字符串

    Returns:
        解码后的 payload（不包含签名验证）
    """
    return jwt.decode(token, options={"verify_signature": False})


def get_token_expiry(token: str) -> Optional[int]:
    """
    获取 Token 的过期时间戳

    Args:
        token: JWT token 字符串

    Returns:
        过期时间戳（Unix timestamp），如果无法解析返回 None
    """
    try:
        payload = decode_token_without_verify(token)
        return payload.get("exp")
    except Exception:
        return None


def is_token_expired(token: str) -> bool:
    """
    检查 Token 是否已过期

    Args:
        token: JWT token 字符串

    Returns:
        True if expired, False otherwise
    """
    expiry = get_token_expiry(token)
    if expiry is None:
        return True
    return time.time() >= expiry


def get_token_user_id(token: str) -> Optional[str]:
    """
    从 Token 中提取用户 ID (sub claim)

    Args:
        token: JWT token 字符串

    Returns:
        用户 ID，如果无法解析返回 None
    """
    try:
        payload = decode_token_without_verify(token)
        return payload.get("sub")
    except Exception:
        return None
