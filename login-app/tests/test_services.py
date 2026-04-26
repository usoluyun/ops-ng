"""
Login App - Services 单元测试
"""
import pytest
import respx
import httpx

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.strapi_client import verify_credentials, get_user_by_id, check_email_exists
from services.hydra_client import get_login_request, accept_login, get_consent_request, accept_consent

STRAPI_URL = "http://localhost:1337"
HYDRA_ADMIN_URL = "http://localhost:4445"


class TestStrapiClient:
    """Strapi 客户端测试"""

    @respx.mock
    async def test_verify_credentials_success(self):
        """verify_credentials 凭证正确返回用户信息"""
        respx.post(f"{STRAPI_URL}/api/auth/local").mock(
            return_value=httpx.Response(
                200,
                json={
                    "jwt": "test-jwt",
                    "user": {
                        "id": 1,
                        "email": "test@yaduo.com",
                        "username": "testuser"
                    }
                }
            )
        )
        user = await verify_credentials("test@yaduo.com", "password123")
        assert user is not None
        assert user["id"] == "1"
        assert user["email"] == "test@yaduo.com"
        assert user["jwt"] == "test-jwt"

    @respx.mock
    async def test_verify_credentials_failure(self):
        """verify_credentials 凭证错误返回 None"""
        respx.post(f"{STRAPI_URL}/api/auth/local").mock(
            return_value=httpx.Response(400)
        )
        user = await verify_credentials("bad@test.com", "wrong")
        assert user is None

    @respx.mock
    async def test_verify_credentials_network_error(self):
        """verify_credentials 网络错误返回 None"""
        respx.post(f"{STRAPI_URL}/api/auth/local").mock(
            side_effect=httpx.ConnectError("Connection failed")
        )
        user = await verify_credentials("test@test.com", "password")
        assert user is None

    @respx.mock
    async def test_get_user_by_id(self):
        """get_user_by_id 返回用户信息"""
        respx.get(f"{STRAPI_URL}/api/users/1").mock(
            return_value=httpx.Response(
                200,
                json={"id": 1, "email": "test@yaduo.com", "username": "test"}
            )
        )
        user = await get_user_by_id("1")
        assert user is not None
        assert user["email"] == "test@yaduo.com"

    @respx.mock
    async def test_check_email_exists_true(self):
        """check_email_exists 邮箱存在返回 True"""
        respx.get(f"{STRAPI_URL}/api/users").mock(
            return_value=httpx.Response(200, json=[{"id": 1, "email": "test@yaduo.com"}])
        )
        exists = await check_email_exists("test@yaduo.com")
        assert exists is True

    @respx.mock
    async def test_check_email_exists_false(self):
        """check_email_exists 邮箱不存在返回 False"""
        respx.get(f"{STRAPI_URL}/api/users").mock(
            return_value=httpx.Response(200, json=[])
        )
        exists = await check_email_exists("notexist@yaduo.com")
        assert exists is False


class TestHydraClient:
    """Hydra 客户端测试"""

    @respx.mock
    async def test_get_login_request(self):
        """get_login_request 返回登录请求信息"""
        respx.get(f"{HYDRA_ADMIN_URL}/admin/oauth2/auth/requests/login").mock(
            return_value=httpx.Response(
                200,
                json={"challenge": "test-challenge", "subject": "user-1"}
            )
        )
        result = await get_login_request("test-challenge")
        assert result["challenge"] == "test-challenge"
        assert result["subject"] == "user-1"

    @respx.mock
    async def test_accept_login(self):
        """accept_login 返回 redirect_to URL"""
        respx.put(f"{HYDRA_ADMIN_URL}/admin/oauth2/auth/requests/login/accept").mock(
            return_value=httpx.Response(
                200,
                json={"redirect_to": "http://hydra/oauth2/auth?consent=abc"}
            )
        )
        redirect = await accept_login("test-challenge", "user-1")
        assert "consent=abc" in redirect

    @respx.mock
    async def test_get_consent_request(self):
        """get_consent_request 返回 consent 请求信息"""
        respx.get(f"{HYDRA_ADMIN_URL}/admin/oauth2/auth/requests/consent").mock(
            return_value=httpx.Response(
                200,
                json={
                    "challenge": "consent-challenge",
                    "subject": "user-1",
                    "requested_scope": ["openid", "offline"]
                }
            )
        )
        result = await get_consent_request("consent-challenge")
        assert result["subject"] == "user-1"
        assert "openid" in result["requested_scope"]

    @respx.mock
    async def test_accept_consent(self):
        """accept_consent 返回 redirect_to URL"""
        respx.put(f"{HYDRA_ADMIN_URL}/admin/oauth2/auth/requests/consent/accept").mock(
            return_value=httpx.Response(
                200,
                json={"redirect_to": "http://client/callback?code=xyz"}
            )
        )
        redirect = await accept_consent(
            "consent-challenge",
            "user-1",
            ["openid", "offline"]
        )
        assert "code=xyz" in redirect
