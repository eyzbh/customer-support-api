
import os
import secrets

from fastapi import Header, HTTPException, status


def get_api_users() -> dict[str, str]:
    """Load API keys and their server-configured identities.

    SUPPORT_API_USERS format:
        key1:user1,key2:user2

    SUPPORT_API_REVIEWERS format:
        reviewer1,admin1
    """
    raw_users = os.getenv("SUPPORT_API_USERS", "")
    users: dict[str, str] = {}

    for entry in raw_users.split(","):
        if ":" not in entry:
            continue

        api_key, username = entry.split(":", 1)
        api_key = api_key.strip()
        username = username.strip()

        if api_key and username:
            users[api_key] = username

    # Backward compatibility for existing development and tests.
    legacy_key = os.getenv("SUPPORT_API_KEY")
    if legacy_key:
        users.setdefault(legacy_key, "api-user")

    return users


def require_api_key(
    authorization: str | None = Header(default=None),
) -> str:
    users = get_api_users()

    if not users:
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

    for api_key, username in users.items():
        if secrets.compare_digest(provided_api_key, api_key):
            return username

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_reviewer(
    reviewer: str = __import__("fastapi").Depends(require_api_key),
) -> str:
    """Require an authenticated identity configured as a reviewer."""
    reviewers = {
        name.strip()
        for name in os.getenv("SUPPORT_API_REVIEWERS", "").split(",")
        if name.strip()
    }

    if reviewer not in reviewers:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Reviewer permission required.",
        )

    return reviewer
