"""
Login App - Consent 路由单元测试
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

HYDRA_ADMIN_URL = "http://localhost:4445"


class TestConsent:
    """GET /consent 路由测试"""

    @respx.mock
    def test_consent_auto_accepts_and_redirects(self):
        """GET /consent?consent_challenge=xxx 应自动接受并重定向"""
        respx.get(f"{HYDRA_ADMIN_URL}/admin/oauth2/auth/requests/consent").mock(
            return_value=httpx.Response(
                200,
                json={
                    "challenge": "consent-challenge",
                    "subject": "1",
                    "requested_scope": ["openid", "offline"],
                    "login_challenge": "login-challenge"
                }
            )
        )
        respx.put(f"{HYDRA_ADMIN_URL}/admin/oauth2/auth/requests/consent/accept").mock(
            return_value=httpx.Response(
                200,
                json={"redirect_to": "http://localhost:3000/callback?code=authcode123"}
            )
        )
        resp = client.get("/consent?consent_challenge=consent-challenge", follow_redirects=False)
        assert resp.status_code == 302
        assert "code=authcode123" in resp.headers["location"]

    @respx.mock
    def test_consent_without_subject_redirects_to_login(self):
        """GET /consent 没有 subject（未登录）应重定向到登录页"""
        respx.get(f"{HYDRA_ADMIN_URL}/admin/oauth2/auth/requests/consent").mock(
            return_value=httpx.Response(
                200,
                json={
                    "challenge": "consent-challenge",
                    "subject": "",  # 未登录
                    "requested_scope": ["openid", "offline"],
                    "login_challenge": "login-challenge"
                }
            )
        )
        resp = client.get("/consent?consent_challenge=consent-challenge", follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" in resp.headers["location"]

    @respx.mock
    def test_consent_hydra_error_returns_error_json(self):
        """GET /consent Hydra 请求失败返回错误 JSON"""
        respx.get(f"{HYDRA_ADMIN_URL}/admin/oauth2/auth/requests/consent").mock(
            return_value=httpx.Response(500)
        )
        resp = client.get("/consent?consent_challenge=bad-challenge", follow_redirects=False)
        assert resp.status_code == 200  # 返回 JSON 错误，不是 500
        data = resp.json()
        assert "error" in data
        assert data["code"] == "HYDRA_ERROR"

    @respx.mock
    def test_consent_accept_error_returns_error_json(self):
        """GET /consent accept 失败返回错误 JSON"""
        respx.get(f"{HYDRA_ADMIN_URL}/admin/oauth2/auth/requests/consent").mock(
            return_value=httpx.Response(
                200,
                json={
                    "challenge": "consent-challenge",
                    "subject": "1",
                    "requested_scope": ["openid"]
                }
            )
        )
        respx.put(f"{HYDRA_ADMIN_URL}/admin/oauth2/auth/requests/consent/accept").mock(
            return_value=httpx.Response(500)
        )
        resp = client.get("/consent?consent_challenge=consent-challenge", follow_redirects=False)
        assert resp.status_code == 200
        data = resp.json()
        assert "error" in data
        assert data["code"] == "HYDRA_ERROR"


class TestConsentReject:
    """POST /consent/reject 路由测试"""

    @respx.mock
    def test_consent_reject_redirects(self):
        """POST /consent/reject 应拒绝并重定向"""
        respx.put(f"{HYDRA_ADMIN_URL}/admin/oauth2/auth/requests/consent/reject").mock(
            return_value=httpx.Response(
                200,
                json={"redirect_to": "http://localhost:3000/callback?error=access_denied"}
            )
        )
        resp = client.post(
            "/consent/reject?consent_challenge=test-challenge",
            follow_redirects=False
        )
        assert resp.status_code == 302
        assert "error=access_denied" in resp.headers["location"]

    @respx.mock
    def test_consent_reject_error_returns_json(self):
        """POST /consent/reject Hydra 错误返回 JSON"""
        respx.put(f"{HYDRA_ADMIN_URL}/admin/oauth2/auth/requests/consent/reject").mock(
            return_value=httpx.Response(500)
        )
        resp = client.post("/consent/reject?consent_challenge=bad-challenge")
        assert resp.status_code == 200
        data = resp.json()
        assert "error" in data
        assert data["code"] == "HYDRA_ERROR"
