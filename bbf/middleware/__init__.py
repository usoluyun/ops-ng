"""
Middleware 模块
包含认证和权限相关的中间件
"""
from .auth import AuthMiddleware, jwt_auth_middleware, error_response, SKIP_AUTH_PATHS
from .jwt_utils import (
    get_jwks_client,
    verify_token,
    decode_token_without_verify,
    get_token_expiry,
    is_token_expired,
    get_token_user_id,
)
from .permissions import (
    PermissionDenied,
    get_user_permissions,
    get_user_roles,
    require_auth,
    require_roles,
    require_permissions,
    require_any_permission,
)

__all__ = [
    # Auth middleware
    "AuthMiddleware",
    "jwt_auth_middleware",
    "error_response",
    "SKIP_AUTH_PATHS",
    # JWT utils
    "get_jwks_client",
    "verify_token",
    "decode_token_without_verify",
    "get_token_expiry",
    "is_token_expired",
    "get_token_user_id",
    # Permissions
    "PermissionDenied",
    "get_user_permissions",
    "get_user_roles",
    "require_auth",
    "require_roles",
    "require_permissions",
    "require_any_permission",
]
