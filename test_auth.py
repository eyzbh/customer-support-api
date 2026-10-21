
import pytest
from fastapi import HTTPException

from auth import get_api_users, require_api_key, require_reviewer


@pytest.fixture
def auth_environment(monkeypatch):
    monkeypatch.setenv(
        "SUPPORT_API_USERS",
        "reviewer-key:reviewer-1,agent-key:support-agent",
    )
    monkeypatch.setenv("SUPPORT_API_REVIEWERS", "reviewer-1")
    monkeypatch.delenv("SUPPORT_API_KEY", raising=False)


def test_get_api_users_loads_configured_users(auth_environment):
    users = get_api_users()

    assert users == {
        "reviewer-key": "reviewer-1",
        "agent-key": "support-agent",
    }


def test_missing_authorization_is_rejected(auth_environment):
    with pytest.raises(HTTPException) as exc_info:
        require_api_key(None)

    assert exc_info.value.status_code == 401
    assert exc_info.value.headers["WWW-Authenticate"] == "Bearer"


def test_invalid_api_key_is_rejected(auth_environment):
    with pytest.raises(HTTPException) as exc_info:
        require_api_key("Bearer invalid-key")

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid API key."


def test_valid_api_key_returns_configured_identity(auth_environment):
    identity = require_api_key("Bearer agent-key")

    assert identity == "support-agent"


def test_authentication_fails_if_no_users_are_configured(monkeypatch):
    monkeypatch.delenv("SUPPORT_API_USERS", raising=False)
    monkeypatch.delenv("SUPPORT_API_KEY", raising=False)

    with pytest.raises(HTTPException) as exc_info:
        require_api_key("Bearer any-key")

    assert exc_info.value.status_code == 503


def test_non_reviewer_is_forbidden(auth_environment):
    with pytest.raises(HTTPException) as exc_info:
        require_reviewer("support-agent")

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Reviewer permission required."


def test_configured_reviewer_is_allowed(auth_environment):
    identity = require_reviewer("reviewer-1")

    assert identity == "reviewer-1"

from fastapi.testclient import TestClient

from main import app


def test_ticket_endpoint_rejects_missing_api_key(auth_environment):
    client = TestClient(app)

    response = client.get("/tickets")

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required."


def test_ticket_endpoint_rejects_invalid_api_key(auth_environment):
    client = TestClient(app)

    response = client.get(
        "/tickets",
        headers={"Authorization": "Bearer invalid-key"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid API key."


def test_ticket_endpoint_accepts_valid_api_key(auth_environment):
    client = TestClient(app)

    response = client.get(
        "/tickets",
        headers={"Authorization": "Bearer agent-key"},
    )

    assert response.status_code == 200
