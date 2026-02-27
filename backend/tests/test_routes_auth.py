import pytest
import os
from passlib.context import CryptContext
from fastapi.testclient import TestClient

os.environ["JWT_SECRET_KEY"] = "test-secret-key-that-is-long-enough-for-hs256"
_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
os.environ["SPARK_COACH_PASSWORD_HASH"] = _pwd.hash("testpassword123")

from main import app

client = TestClient(app)


def test_login_success():
    resp = client.post("/api/v1/auth/login", json={"password": "testpassword123"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 604800


def test_login_wrong_password():
    resp = client.post("/api/v1/auth/login", json={"password": "wrongpassword"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Incorrect password"


def test_login_empty_password():
    resp = client.post("/api/v1/auth/login", json={"password": ""})
    assert resp.status_code == 422  # Pydantic validation


def test_protected_endpoint_with_valid_token():
    # Get a valid token
    resp = client.post("/api/v1/auth/login", json={"password": "testpassword123"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    # Use it to access a protected endpoint
    resp = client.get(
        "/api/v1/briefing/quick",
        headers={"Authorization": f"Bearer {token}"}
    )
    # Should not be 401 (may be 500 if briefing service is unavailable in test, that's OK)
    assert resp.status_code != 401


def test_protected_endpoint_without_token():
    resp = client.get(
        "/api/v1/briefing/quick",
        headers={}  # no Authorization header
    )
    assert resp.status_code == 401
