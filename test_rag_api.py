
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_ask_knowledge_returns_answer_and_sources():
    fake_result = {
        "question": "I forgot my password.",
        "answer": "Use the account recovery page.",
        "sources": [
            {
                "title": "Password Recovery",
                "content": (
                    "Customers can reset forgotten passwords "
                    "through the account recovery page."
                ),
                "score": 0.74,
            }
        ],
    }

    with patch("main.answer_question", return_value=fake_result):
        response = client.post(
            "/ask-knowledge",
            json={"question": "I forgot my password."},
        )

    assert response.status_code == 200
    assert response.json() == fake_result


def test_ask_knowledge_rejects_empty_question():
    response = client.post(
        "/ask-knowledge",
        json={"question": ""},
    )

    assert response.status_code == 422


def test_ask_knowledge_handles_model_failure():
    with patch(
        "main.answer_question",
        side_effect=RuntimeError("Local model failed."),
    ):
        response = client.post(
            "/ask-knowledge",
            json={"question": "I forgot my password."},
        )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Knowledge service is temporarily unavailable."
    }
def test_ask_knowledge_rate_limit():
    from fastapi.testclient import TestClient
    import main

    client = TestClient(main.app)

    # Send requests until the configured limit is exceeded.
    responses = [
        client.post(
            "/ask-knowledge",
            json={"question": "What is the refund policy?"},
        )
        for _ in range(11)
    ]

    assert any(response.status_code == 429 for response in responses)