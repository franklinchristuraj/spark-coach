"""
Authentication routes for SPARK Coach API.
Single endpoint: POST /api/v1/auth/login
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from auth import verify_password, create_access_token
from config import settings

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class LoginRequest(BaseModel):
    password: str

    @field_validator("password")
    @classmethod
    def password_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Password cannot be empty")
        return v


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 604800  # 7 days in seconds


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Authenticate with password, receive a 7-day JWT.
    The token should be stored as a cookie and sent as
    'Authorization: Bearer <token>' on subsequent API calls.
    """
    if not settings.SPARK_COACH_PASSWORD_HASH:
        raise HTTPException(
            status_code=500,
            detail="Server not configured: SPARK_COACH_PASSWORD_HASH is not set",
        )
    if not verify_password(request.password, settings.SPARK_COACH_PASSWORD_HASH):
        raise HTTPException(status_code=401, detail="Incorrect password")
    token = create_access_token()
    return LoginResponse(access_token=token)
