"""
Login App - Login 路由单元测试
"""
import pytest
import respx
import httpx
from fastapi.testclient import TestClient

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app, raise_server_exceptions=False)

STRAPI_URL = "http://localhost:1337"
HYDRA_ADMIN_URL = "http://localhost:4445"


class TestLoginForm:
    """GET /login 路由测试"""

    def test_health_endpoint(self):
        """健康检查应该返回 ok"""
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    @respx.mock
    def test_login_form_renders_with_valid_challenge(self):
        """GET /login?login_challenge=xxx 应返回 HTML 表单"""
        respx.get(f"{HYDRA_ADMIN_URL}/admin/oauth2/auth/requests/login").mock(
            return_value=httpx.Response(
                200,
                json={"challenge": "test-challenge", "subject": ""}
            )
        )
        resp = client.get("/login?login_challenge=test-challenge", follow_redirects=False)
        assert resp.status_code == 200
        assert "亚朵运维系统" in resp.text
        assert 'name="login_challenge"' in resp.text

    @respx.mock
    def test_login_form_without_challenge_renders(self):
        """GET /login 不带 challenge 参数也应返回表单"""
        resp = client.get("/login", follow_redirects=False)
        assert resp.status_code == 200
        assert "亚朵运维系统" in resp.text


class TestLoginSubmit:
    """POST /login 路由测试"""

    @respx.mock
    def test_login_post_valid_credentials_redirects(self):
        """POST /login 凭证正确，应重定向到 Hydra redirect_to"""
        respx.post(f"{STRAPI_URL}/api/auth/local").mock(
            return_value=httpx.Response(
                200,
                json={
                    "jwt": "fake-jwt-token",
                    "user": {
                        "id": 1,
                        "email": "test@yaduo.com",
                        "username": "testuser"
                    }
                }
            )
        )
        respx.put(f"{HYDRA_ADMIN_URL}/admin/oauth2/auth/requests/login/accept").mock(
            return_value=httpx.Response(
                200,
                json={"redirect_to": "http://localhost:4444/oauth2/auth?consent_challenge=abc"}
            )
        )
        resp = client.post(
            "/login",
            data={
                "login_challenge": "test-challenge",
                "identifier": "test@yaduo.com",
                "password": "correct"
            },
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert "consent_challenge" in resp.headers["location"]

    @respx.mock
    def test_login_post_invalid_credentials_returns_401(self):
        """POST /login 凭证错误，应返回 401 并显示错误信息"""
        respx.post(f"{STRAPI_URL}/api/auth/local").mock(
            return_value=httpx.Response(
                400,
                json={"error": {"message": "Invalid identifier or password"}}
            )
        )
        resp = client.post(
            "/login",
            data={
                "login_challenge": "test-challenge",
                "identifier": "bad@test.com",
                "password": "wrong"
            },
            follow_redirects=False,
        )
        assert resp.status_code == 401
        assert "账号或密码错误" in resp.text

    @respx.mock
    def test_login_without_oauth_redirects_json(self):
        """POST /login 不带 login_challenge，凭证正确返回 JSON"""
        respx.post(f"{STRAPI_URL}/api/auth/local").mock(
            return_value=httpx.Response(
                200,
                json={
                    "jwt": "fake-jwt-token",
                    "user": {
                        "id": 1,
                        "email": "test@yaduo.com",
                        "username": "testuser"
                    }
                }
            )
        )
        resp = client.post(
            "/login",
            data={
                "identifier": "test@yaduo.com",
                "password": "correct"
            },
            follow_redirects=False,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["user"]["email"] == "test@yaduo.com"


class TestApiLogin:
    """POST /api/login 路由测试"""

    @respx.mock
    def test_api_login_valid_credentials(self):
        """POST /api/login 凭证正确返回用户信息"""
        respx.post(f"{STRAPI_URL}/api/auth/local").mock(
            return_value=httpx.Response(
                200,
                json={
                    "jwt": "fake-jwt-token",
                    "user": {
                        "id": 1,
                        "email": "test@yaduo.com",
                        "username": "testuser"
                    }
                }
            )
        )
        resp = client.post(
            "/api/login",
            json={
                "identifier": "test@yaduo.com",
                "password": "correct"
            }
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

    @respx.mock
    def test_api_login_invalid_credentials(self):
        """POST /api/login 凭证错误返回 401"""
        respx.post(f"{STRAPI_URL}/api/auth/local").mock(
            return_value=httpx.Response(400)
        )
        resp = client.post(
            "/api/login",
            json={
                "identifier": "bad@test.com",
                "password": "wrong"
            }
        )
        assert resp.status_code == 401

    def test_api_login_missing_fields(self):
        """POST /api/login 缺少字段返回 400"""
        resp = client.post("/api/login", json={"identifier": "test@test.com"})
        assert resp.status_code == 400
        assert resp.json()["code"] == "MISSING_CREDENTIALS"


class TestLogout:
    """GET /logout 路由测试"""

    def test_logout_returns_ok(self):
        """GET /logout 应返回 logged out 状态"""
        resp = client.get("/logout")
        assert resp.status_code == 200
        assert resp.json()["status"] == "logged out"
