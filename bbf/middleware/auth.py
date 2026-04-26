"""
认证中间件
JWT 验证中间件，基于 ORY Hydra JWKS

功能：
- 从 Authorization header 提取 Bearer Token
- 通过 Hydra JWKS 端点验证 Token 签名
- 验证 Token 有效期
- 将用户信息注入 request.state
- 白名单路径跳过认证
"""
import os
import time
from typing import Callable, Optional, Set

import httpx
import jwt
from fastapi import Request
from fastapi.responses import JSONResponse
from jwt import PyJWKClient, PyJWKClientError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

HYDRA_PUBLIC_URL = os.getenv("HYDRA_PUBLIC_URL", "http://localhost:4444")
JWKS_URI = f"{HYDRA_PUBLIC_URL}/.well-known/jwks.json"

# JWKS 缓存
_jwks_client: Optional[PyJWKClient] = None
_jwks_cache_time: float = 0
JWKS_CACHE_TTL = 3600  # 1 hour

# 白名单路径（无需认证）
SKIP_AUTH_PATHS: Set[str] = {
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/metrics",
}


def get_jwks_client() -> PyJWKClient:
    """获取 JWKS 客户端，支持缓存（1小时）"""
    global _jwks_client, _jwks_cache_time
    now = time.time()
    if _jwks_client is None or (now - _jwks_cache_time) > JWKS_CACHE_TTL:
        _jwks_client = PyJWKClient(JWKS_URI)
        _jwks_cache_time = now
    return _jwks_client


def error_response(message: str, code: str, status: int = 401) -> JSONResponse:
    """生成统一格式的错误响应"""
    return JSONResponse(
        status_code=status,
        content={"error": message, "code": code},
    )


class AuthMiddleware(BaseHTTPMiddleware):
    """
    JWT 认证中间件

    验证请求头中的 Bearer Token，将解码后的用户信息注入 request.state

    Attributes:
        app: ASGI 应用

    request.state 属性:
        user_id: 用户 ID (sub claim)
        token_payload: 完整的 Token payload
        token_expiry: Token 过期时间戳
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable):
        # 跳过白名单路径
        if request.url.path in SKIP_AUTH_PATHS:
            return await call_next(request)

        # 提取 Authorization header
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return error_response(
                "Missing or invalid Authorization header",
                "MISSING_TOKEN"
            )

        token = auth_header[len("Bearer "):]

        if not token:
            return error_response(
                "Missing or invalid Authorization header",
                "MISSING_TOKEN"
            )

        try:
            # 验证 Token
            jwks_client = get_jwks_client()
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                options={"verify_aud": False},
            )

            # 注入用户信息到 request.state
            request.state.user_id = payload.get("sub", "")
            request.state.token_payload = payload

            # 计算过期时间
            if "exp" in payload:
                request.state.token_expiry = payload["exp"]
            else:
                request.state.token_expiry = None

        except jwt.ExpiredSignatureError:
            return error_response("Token has expired", "TOKEN_EXPIRED")
        except jwt.InvalidTokenError as e:
            return error_response(f"Invalid token: {str(e)}", "INVALID_TOKEN")
        except PyJWKClientError as e:
            return error_response(f"JWKS error: {str(e)}", "JWKS_ERROR")
        except Exception as e:
            return error_response(f"Authentication failed: {str(e)}", "AUTH_FAILED")

        response = await call_next(request)
        return response


async def jwt_auth_middleware(request: Request, call_next: Callable):
    """
    兼容旧版函数的 jwt_auth_middleware
    新代码应使用 AuthMiddleware 类
    """
    return await AuthMiddleware(lambda x: x).dispatch(request, call_next)
