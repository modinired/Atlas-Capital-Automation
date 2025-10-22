"""
Security utilities for the Terry Delmonaco Presents: AI service.

This module implements a simple API key authentication mechanism. Clients must include
the correct API key in the `X-API-Key` header. The expected key is configured via
the `API_KEY` environment variable. If no key is configured, authentication is disabled.

See also: FastAPI dependency injection for security dependencies and the Starlette
`HTTPException` class used here to return appropriate error responses.
"""

from fastapi import Header, HTTPException, Security
from starlette.status import HTTP_401_UNAUTHORIZED
from app.config import settings


async def get_api_key(api_key: str = Header(default=None, alias="X-API-Key")) -> str:
    """Validate the provided API key.

    Args:
        api_key: The value of the `X-API-Key` header sent by the client.

    Returns:
        The API key if validation succeeds.

    Raises:
        HTTPException: If authentication fails or the key is missing when authentication
        is enabled.
    """
    expected_key = settings.api_key
    if expected_key is None:
        # Authentication disabled; accept any key or lack thereof.
        return api_key or ""
    if api_key is None or api_key != expected_key:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "API-Key"},
        )
    return api_key