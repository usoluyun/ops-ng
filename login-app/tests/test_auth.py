"""
测试认证功能
包括注册和登录
"""
import pytest
import respx
import httpx
from fastapi.testclient import TestClient

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import app

client = TestClient(app, raise_server_exceptions=False)

STRAPI_URL = "http://localhost:1337"
HYDRA_ADMIN_URL = "http://localhost:4445"


class TestRegister:
    """用户注册测试"""

    def test_register_form_renders(self):
        """GET /register 应返回注册表单"""
        resp = client.get("/register")
        assert resp.status_code == 200
        assert "创建账号" in resp.text
        assert 'name="email"' in resp.text
        assert 'name="password"' in resp.text
        assert 'name="username"' in resp.text

    @respx.mock
    def test_register_success(self):
        """注册成功应返回成功页面"""
        # 模拟邮箱检查（不存在）
        respx.get(f"{STRAPI_URL}/api/users").mock(
            return_value=httpx.Response(200, json=[])
        )
        # 模拟用户创建
        respx.post(f"{STRAPI_URL}/api/auth/register").mock(
            return_value=httpx.Response(201, json={
                "jwt": "test-jwt",
                "user": {
                    "id": 1,
                    "email": "test@example.com",
                    "username": "testuser",
                }
            })
        )

        resp = client.post(
            "/register",
            data={
                "email": "test@example.com",
                "password": "Test@123456",
                "username": "testuser",
            },
        )
        assert resp.status_code == 200
        assert "注册成功" in resp.text

    @respx.mock
    def test_register_email_exists(self):
        """邮箱已存在应返回错误"""
        # 模拟邮箱已存在
        respx.get(f"{STRAPI_URL}/api/users").mock(
            return_value=httpx.Response(200, json=[{"id": 1, "email": "test@example.com"}])
        )

        resp = client.post(
            "/register",
            data={
                "email": "test@example.com",
                "password": "Test@123456",
                "username": "testuser",
            },
        )
        assert resp.status_code == 400
        assert "已被注册" in resp.text

    def test_register_weak_password(self):
        """弱密码应返回错误"""
        resp = client.post(
            "/register",
            data={
                "email": "test@example.com",
                "password": "weak",
                "username": "testuser",
            },
        )
        assert resp.status_code == 400
        assert "强度不足" in resp.text


class TestLogin:
    """用户登录测试"""

    def test_login_form_renders(self):
        """GET /login 应返回登录表单"""
        resp = client.get("/login")
        assert resp.status_code == 200
        assert "亚朵运维系统" in resp.text
        assert 'name="identifier"' in resp.text
        assert 'name="password"' in resp.text

    @respx.mock
    def test_login_success(self):
        """登录成功应重定向到 Hydra"""
        # 模拟 Hydra login request
        respx.get(f"{HYDRA_ADMIN_URL}/admin/oauth2/auth/requests/login").mock(
            return_value=httpx.Response(200, json={"challenge": "test-challenge", "subject": ""})
        )
        # 模拟 Hydra accept login
        respx.put(f"{HYDRA_ADMIN_URL}/admin/oauth2/auth/requests/login/accept").mock(
            return_value=httpx.Response(200, json={
                "redirect_to": "http://localhost:4444/oauth2/auth?consent_challenge=abc"
            })
        )
        # 模拟 Strapi 凭证验证
        respx.post(f"{STRAPI_URL}/api/auth/local").mock(
            return_value=httpx.Response(200, json={
                "jwt": "fake-jwt",
                "user": {
                    "id": 1,
                    "email": "test@yaduo.com",
                    "username": "testuser"
                }
            })
        )

        resp = client.post(
            "/login",
            data={
                "login_challenge": "test-challenge",
                "identifier": "test@yaduo.com",
                "password": "correct",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert "consent_challenge" in resp.headers.get("location", "")

    @respx.mock
    def test_login_invalid_credentials(self):
        """无效凭证应返回错误"""
        # 模拟 Hydra login request
        respx.get(f"{HYDRA_ADMIN_URL}/admin/oauth2/auth/requests/login").mock(
            return_value=httpx.Response(200, json={"challenge": "test-challenge", "subject": ""})
        )
        # 模拟 Strapi 凭证验证失败
        respx.post(f"{STRAPI_URL}/api/auth/local").mock(
            return_value=httpx.Response(400, json={"error": {"message": "Invalid identifier or password"}})
        )

        resp = client.post(
            "/login",
            data={
                "login_challenge": "test-challenge",
                "identifier": "bad@test.com",
                "password": "wrong",
            },
        )
        assert resp.status_code == 401
        assert "账号或密码错误" in resp.text


class TestLogout:
    """登出测试"""

    def test_logout_returns_ok(self):
        """GET /logout 应返回成功"""
        resp = client.get("/logout")
        assert resp.status_code == 200
        assert resp.json()["status"] == "logged out"


class TestHealth:
    """健康检查测试"""

    def test_health_endpoint(self):
        """GET /health 应返回 OK"""
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
