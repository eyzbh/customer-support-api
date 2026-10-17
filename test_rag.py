
from unittest.mock import Mock

import pytest

import rag_service


def test_rag_returns_answer_and_sources(monkeypatch):
    fake_sources = [
        {
            "title": "Password Recovery",
            "content": "Customers can reset forgotten passwords through the account recovery page.",
            "score": 0.74,
        }
    ]

    monkeypatch.setattr(
    rag_service,
    "search_knowledge_base",
    lambda question, top_k=2, min_score=0.0: fake_sources,
)
    fake_response = {
        "message": {
            "content": "Use the account recovery page to reset your password."
        }
    }

    fake_chat = Mock(return_value=fake_response)

    monkeypatch.setattr(rag_service.ollama, "chat", fake_chat)

    result = rag_service.answer_question("I forgot my password.")

    assert result["answer"] == (
        "Use the account recovery page to reset your password."
    )
    assert result["sources"][0]["title"] == "Password Recovery"
    assert result["sources"][0]["score"] == 0.74

    # Confirm the retrieved document was passed to the model.
    chat_messages = fake_chat.call_args.kwargs["messages"]
    assert "Password Recovery" in chat_messages[1]["content"]


def test_rag_rejects_empty_question():
    with pytest.raises(ValueError, match="must not be empty"):
        rag_service.answer_question("   ")

def test_rag_returns_fallback_when_no_sources(monkeypatch):
    monkeypatch.setattr(
        rag_service,
        "search_knowledge_base",
        lambda question, top_k=2, min_score=0.0: [],
    )

    fake_chat = Mock()
    monkeypatch.setattr(rag_service.ollama, "chat", fake_chat)

    result = rag_service.answer_question(
        "Does the company offer student discounts?"
    )

    assert result["sources"] == []
    assert "not have enough information" in result["answer"].lower()
    fake_chat.assert_not_called()
