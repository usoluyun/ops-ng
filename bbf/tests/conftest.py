import pytest
import jwt
import time
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from fastapi.testclient import TestClient

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


@pytest.fixture(scope="session")
def rsa_private_key():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return key


@pytest.fixture(scope="session")
def rsa_public_key(rsa_private_key):
    return rsa_private_key.public_key()


@pytest.fixture(scope="session")
def valid_token(rsa_private_key):
    priv_pem = rsa_private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    )
    payload = {
        "sub": "user-123",
        "iss": "http://localhost:4444",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
        "scp": ["openid", "offline"],
    }
    return jwt.encode(payload, priv_pem, algorithm="RS256")


@pytest.fixture(scope="session")
def expired_token(rsa_private_key):
    priv_pem = rsa_private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    )
    payload = {
        "sub": "user-123",
        "iss": "http://localhost:4444",
        "iat": int(time.time()) - 7200,
        "exp": int(time.time()) - 3600,  # expired
    }
    return jwt.encode(payload, priv_pem, algorithm="RS256")
