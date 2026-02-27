import pytest
import os
from datetime import datetime, timedelta, timezone

# Set test env vars before importing anything
os.environ["JWT_SECRET_KEY"] = "test-secret-key-that-is-long-enough-for-hs256"
os.environ["SPARK_COACH_PASSWORD_HASH"] = ""

from passlib.context import CryptContext

# Generate a real test hash once
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
TEST_HASH = _pwd_context.hash("correctpassword")


def test_verify_password_correct():
    from auth import verify_password
    assert verify_password("correctpassword", TEST_HASH) is True


def test_verify_password_wrong():
    from auth import verify_password
    assert verify_password("wrongpassword", TEST_HASH) is False


def test_create_access_token_returns_string():
    from auth import create_access_token
    token = create_access_token()
    assert isinstance(token, str)
    assert len(token) > 0


def test_create_access_token_is_decodable():
    from auth import create_access_token
    from jose import jwt
    token = create_access_token()
    payload = jwt.decode(token, "test-secret-key-that-is-long-enough-for-hs256", algorithms=["HS256"])
    assert payload["sub"] == "franklin"


def test_create_access_token_expires_in_7_days():
    from auth import create_access_token
    from jose import jwt
    token = create_access_token()
    payload = jwt.decode(token, "test-secret-key-that-is-long-enough-for-hs256", algorithms=["HS256"])
    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    now = datetime.now(timezone.utc)
    diff = exp - now
    # Should be approximately 7 days (allow 1 minute tolerance)
    assert timedelta(days=6, hours=23) < diff < timedelta(days=7, minutes=1)
