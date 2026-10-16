
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from main import app
from database import get_connection

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_database():
    with get_connection() as connection:
        connection.execute("DELETE FROM tickets")
        connection.execute(
            "DELETE FROM sqlite_sequence WHERE name = 'tickets'"
        )


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_create_ticket():
    response = client.post(
        "/tickets",
        json={
            "customer_name": "Abebe Bekele",
            "email": "abebe@example.com",
            "subject": "Cannot log in",
            "description": "I cannot access my account after resetting my password.",
            "priority": "high",
        },
    )

    assert response.status_code == 201
    assert response.json()["id"] == 1
    assert response.json()["status"] == "open"


def test_get_ticket():
    create_response = client.post(
        "/tickets",
        json={
            "customer_name": "Abebe Bekele",
            "email": "abebe@example.com",
            "subject": "Cannot log in",
            "description": "I cannot access my account after resetting my password.",
            "priority": "high",
        },
    )

    ticket_id = create_response.json()["id"]
    response = client.get(f"/tickets/{ticket_id}")

    assert response.status_code == 200
    assert response.json()["customer_name"] == "Abebe Bekele"


def test_close_ticket():
    create_response = client.post(
        "/tickets",
        json={
            "customer_name": "Abebe Bekele",
            "email": "abebe@example.com",
            "subject": "Cannot log in",
            "description": "I cannot access my account after resetting my password.",
            "priority": "high",
        },
    )

    ticket_id = create_response.json()["id"]
    response = client.patch(
        f"/tickets/{ticket_id}",
        json={"status": "closed"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "closed"


def test_get_missing_ticket():
    response = client.get("/tickets/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Ticket not found"


def test_invalid_email():
    response = client.post(
        "/tickets",
        json={
            "customer_name": "Abebe Bekele",
            "email": "not-an-email",
            "subject": "Cannot log in",
            "description": "I cannot access my account after resetting my password.",
            "priority": "high",
        },
    )

    assert response.status_code == 422

def test_sentiment_endpoint():
    with patch(
        "main.analyze_sentiment",
        return_value={"sentiment": "positive", "score": 0.95},
    ):
        response = client.post(
            "/sentiment",
            json={
                "text": "The support team solved my problem quickly."
            },
        )

    assert response.status_code == 200
    assert response.json() == {
        "text": "The support team solved my problem quickly.",
        "sentiment": "positive",
        "score": 0.95,
    }


def test_sentiment_endpoint_rejects_empty_text():
    response = client.post(
        "/sentiment",
        json={"text": ""},
    )

    assert response.status_code == 422

def test_sentiment_endpoint_handles_model_failure():
    with patch(
        "main.analyze_sentiment",
        side_effect=RuntimeError("Sentiment analysis failed."),
    ):
        response = client.post(
            "/sentiment",
            json={"text": "The service was helpful."},
        )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Sentiment analysis is temporarily unavailable."
    }

def test_analyze_ticket_endpoint():
    with patch(
        "main.analyze_ticket",
        return_value={
            "category": "billing",
            "priority": "high",
            "suggested_reply": "We will review the duplicate charge.",
        },
    ):
        response = client.post(
            "/analyze-ticket",
            json={
                "message": "I was charged twice for my subscription."
            },
        )

    assert response.status_code == 200
    assert response.json() == {
        "category": "billing",
        "priority": "high",
        "suggested_reply": "We will review the duplicate charge.",
    }


def test_analyze_ticket_handles_model_failure():
    with patch(
        "main.analyze_ticket",
        side_effect=RuntimeError("Local model failed."),
    ):
        response = client.post(
            "/analyze-ticket",
            json={"message": "I cannot access my account."},
        )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Ticket analysis is temporarily unavailable."
    }
