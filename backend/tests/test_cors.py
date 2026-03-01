import os

# Must set env vars before any project imports
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-that-is-long-enough-for-hs256")
# bcrypt hash of "testpassword123" (work factor 12).
# Must stay in sync with the password used in test_routes_auth.py.
# If test_routes_auth.py changes its test password, regenerate this hash with:
#   python3 -c "from passlib.context import CryptContext; print(CryptContext(schemes=['bcrypt']).hash('newpassword'))"
os.environ["SPARK_COACH_PASSWORD_HASH"] = "$2b$12$CLefaqNbKaBNkWYFd88YZerlgu4bKpSuXUkHBjMK8n46KvbjaML.2"
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("MCP_SERVER_URL", "http://localhost:3000")
os.environ.setdefault("MCP_API_KEY", "")
os.environ.setdefault("GEMINI_API_KEY", "fake-key")
os.environ["ALLOWED_ORIGINS"] = "http://localhost:3000,http://localhost:3001,https://coach.ziksaka.com"

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_cors_allows_localhost():
    resp = client.get("/health", headers={"Origin": "http://localhost:3000"})
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_cors_allows_production_origin():
    resp = client.get("/health", headers={"Origin": "https://coach.ziksaka.com"})
    assert resp.headers.get("access-control-allow-origin") == "https://coach.ziksaka.com"


def test_cors_blocks_unknown_origin():
    resp = client.get("/health", headers={"Origin": "https://evil.example.com"})
    # Unknown origins must be rejected — header must be absent entirely
    assert resp.headers.get("access-control-allow-origin") is None
