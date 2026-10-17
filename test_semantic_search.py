
import pytest

from semantic_search import search_knowledge_base


def test_password_query_returns_password_recovery_first():
    results = search_knowledge_base(
        "I forgot my password and cannot log in."
    )

    assert len(results) == 2
    assert results[0]["title"] == "Password Recovery"
    assert results[0]["score"] > results[1]["score"]


def test_search_returns_requested_number_of_results():
    results = search_knowledge_base(
        "How can I pay my invoice?",
        top_k=1,
    )

    assert len(results) == 1


def test_empty_query_is_rejected():
    with pytest.raises(ValueError, match="must not be empty"):
        search_knowledge_base("   ")


def test_invalid_top_k_is_rejected():
    with pytest.raises(ValueError, match="at least 1"):
        search_knowledge_base("password help", top_k=0)
