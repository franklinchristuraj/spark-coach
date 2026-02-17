"""
Authentication middleware for SPARK Coach API
MVP: Simple API key check
Week 2: Migrate to JWT
"""
from fastapi import Request, HTTPException, Security
from fastapi.security import APIKeyHeader
from config import settings

# API Key header security scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)):
    """
    MVP auth: simple API key check

    Args:
        api_key: API key from X-API-Key header

    Raises:
        HTTPException: If API key is invalid or missing
    """
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Include X-API-Key header."
        )

    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )

    return api_key


async def verify_api_key_optional(api_key: str = Security(api_key_header)):
    """
    Optional API key verification for public endpoints
    Returns None if no key provided, validates if present
    """
    if not api_key:
        return None

    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )

    return api_key
