import pytest
import respx
import httpx
import json
import base64
from unittest.mock import patch, MagicMock
from cryptography.hazmat.primitives import serialization
from fastapi.testclient import TestClient

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import app

client = TestClient(app, raise_server_exceptions=False)


def test_health_no_auth_required():
    resp = client.get("/health")
    assert resp.status_code == 200


def test_missing_token_returns_401():
    resp = client.get("/api/hotels")
    assert resp.status_code == 401
    assert resp.json()["code"] == "MISSING_TOKEN"


def test_invalid_bearer_format_returns_401():
    resp = client.get("/api/hotels", headers={"Authorization": "Basic abc123"})
    assert resp.status_code == 401
    assert resp.json()["code"] == "MISSING_TOKEN"


def test_empty_bearer_token_returns_401():
    resp = client.get("/api/hotels", headers={"Authorization": "Bearer "})
    assert resp.status_code == 401
    assert resp.json()["code"] == "MISSING_TOKEN"


def test_expired_token_returns_401(expired_token, rsa_public_key):
    pub_pem = rsa_public_key.public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    with patch("middleware.auth.get_jwks_client") as mock_get_client:
        mock_signing_key = MagicMock()
        mock_signing_key.key = pub_pem
        mock_client = MagicMock()
        mock_client.get_signing_key_from_jwt = MagicMock(return_value=mock_signing_key)
        mock_get_client.return_value = mock_client
        resp = client.get("/api/hotels", headers={"Authorization": f"Bearer {expired_token}"})
    assert resp.status_code == 401
    assert resp.json()["code"] == "TOKEN_EXPIRED"


@respx.mock
def test_valid_token_passes_to_strapi(valid_token, rsa_public_key):
    pub_pem = rsa_public_key.public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    respx.get("http://localhost:1337/api/hotels").mock(
        return_value=httpx.Response(200, json={"data": [], "meta": {"pagination": {"page": 1, "pageSize": 25, "total": 0}}})
    )
    with patch("middleware.auth.get_jwks_client") as mock_get_client:
        mock_signing_key = MagicMock()
        mock_signing_key.key = pub_pem
        mock_client = MagicMock()
        mock_client.get_signing_key_from_jwt = MagicMock(return_value=mock_signing_key)
        mock_get_client.return_value = mock_client
        resp = client.get("/api/hotels", headers={"Authorization": f"Bearer {valid_token}"})
    assert resp.status_code == 200
