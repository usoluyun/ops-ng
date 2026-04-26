import pytest
import respx
import httpx
from unittest.mock import patch, MagicMock
from cryptography.hazmat.primitives import serialization
from fastapi.testclient import TestClient

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import app

client = TestClient(app, raise_server_exceptions=False)

STRAPI_URL = "http://localhost:1337"

HOTEL_RESPONSE = {
    "data": [
        {"id": 1, "attributes": {"chainId": 1001, "chainName": "亚朵·测试北京", "status": 3}},
        {"id": 2, "attributes": {"chainId": 1002, "chainName": "亚朵·测试上海", "status": 3}},
    ],
    "meta": {"pagination": {"page": 1, "pageSize": 25, "total": 2}},
}


def _mock_auth(valid_token, rsa_public_key):
    pub_pem = rsa_public_key.public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    mock_signing_key = MagicMock()
    mock_signing_key.key = pub_pem
    mock_client = MagicMock()
    mock_client.get_signing_key_from_jwt = MagicMock(return_value=mock_signing_key)
    return patch("middleware.auth.get_jwks_client", return_value=mock_client)


@respx.mock
def test_list_hotels_returns_strapi_data(valid_token, rsa_public_key):
    respx.get(f"{STRAPI_URL}/api/hotels").mock(
        return_value=httpx.Response(200, json=HOTEL_RESPONSE)
    )
    with _mock_auth(valid_token, rsa_public_key):
        resp = client.get("/api/hotels", headers={"Authorization": f"Bearer {valid_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["data"]) == 2
    assert data["data"][0]["attributes"]["chainId"] == 1001


@respx.mock
def test_get_hotel_not_found(valid_token, rsa_public_key):
    respx.get(f"{STRAPI_URL}/api/hotels/999").mock(
        return_value=httpx.Response(404, json={"error": {"message": "Not Found"}})
    )
    with _mock_auth(valid_token, rsa_public_key):
        resp = client.get("/api/hotels/999", headers={"Authorization": f"Bearer {valid_token}"})
    assert resp.status_code == 404


@respx.mock
def test_create_hotel(valid_token, rsa_public_key):
    respx.post(f"{STRAPI_URL}/api/hotels").mock(
        return_value=httpx.Response(200, json={"data": {"id": 3, "attributes": {"chainId": 1003}}})
    )
    with _mock_auth(valid_token, rsa_public_key):
        resp = client.post(
            "/api/hotels",
            json={"chainId": 1003, "chainName": "亚朵·测试广州"},
            headers={"Authorization": f"Bearer {valid_token}"},
        )
    assert resp.status_code == 201


@respx.mock
def test_list_hotels_with_pagination(valid_token, rsa_public_key):
    respx.get(f"{STRAPI_URL}/api/hotels").mock(
        return_value=httpx.Response(200, json=HOTEL_RESPONSE)
    )
    with _mock_auth(valid_token, rsa_public_key):
        resp = client.get("/api/hotels?page=1&page_size=10", headers={"Authorization": f"Bearer {valid_token}"})
    assert resp.status_code == 200


@respx.mock
def test_list_hotel_rooms(valid_token, rsa_public_key):
    rooms_response = {
        "data": [
            {"id": 1, "attributes": {"roomNo": "101", "floor": 1}},
            {"id": 2, "attributes": {"roomNo": "102", "floor": 1}},
        ],
        "meta": {"pagination": {"page": 1, "pageSize": 25, "total": 2}},
    }
    respx.get(f"{STRAPI_URL}/api/rooms").mock(
        return_value=httpx.Response(200, json=rooms_response)
    )
    with _mock_auth(valid_token, rsa_public_key):
        resp = client.get("/api/hotels/1/rooms", headers={"Authorization": f"Bearer {valid_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["data"]) == 2
