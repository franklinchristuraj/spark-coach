import os
import pytest

# Must set env vars before any project imports
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-that-is-long-enough-for-hs256")
# Use the hash for "testpassword123" so test_routes_auth.py works when run in the same process
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
    # Should not echo the unknown origin back
    assert resp.headers.get("access-control-allow-origin") != "https://evil.example.com"
