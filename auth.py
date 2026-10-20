
import os
import secrets

from fastapi import Header, HTTPException, status


def require_api_key(
    authorization: str | None = Header(default=None),
) -> str:
    expected_api_key = os.getenv("SUPPORT_API_KEY")

    if not expected_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API authentication is not configured.",
        )

    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    provided_api_key = authorization.removeprefix("Bearer ").strip()

    if not secrets.compare_digest(provided_api_key, expected_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return "api-user"
