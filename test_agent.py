
import json
from unittest.mock import Mock

import agent


def test_run_agent_rejects_empty_question():
    try:
        agent.run_agent("   ")
    except ValueError as error:
        assert str(error) == "Question must not be empty."
    else:
        raise AssertionError("Expected ValueError")


def test_run_agent_returns_direct_answer_without_tool_call(monkeypatch):
    fake_response = {
        "message": {
            "content": "Hello! How can I help?",
            "tool_calls": [],
        }
    }

    fake_chat = Mock(return_value=fake_response)
    monkeypatch.setattr(agent.ollama, "chat", fake_chat)

    result = agent.run_agent("Hello")

    assert result == "Hello! How can I help?"
    fake_chat.assert_called_once()


def test_run_agent_executes_registered_tool(monkeypatch):
    first_response = {
        "message": {
            "content": "",
            "tool_calls": [
                {
                    "function": {
                        "name": "get_ticket",
                        "arguments": {"ticket_id": 1},
                    }
                }
            ],
        }
    }

    second_response = {
        "message": {
            "content": "Ticket 1 was not found.",
            "tool_calls": [],
        }
    }

    fake_chat = Mock(side_effect=[first_response, second_response])
    fake_get_ticket = Mock(return_value=None)

    monkeypatch.setattr(agent.ollama, "chat", fake_chat)
    monkeypatch.setitem(
        agent.AVAILABLE_FUNCTIONS, "get_ticket", fake_get_ticket
    )

    result = agent.run_agent("Check ticket 1")

    fake_get_ticket.assert_called_once_with(ticket_id=1)
    assert result == "Ticket 1 was not found."
    assert fake_chat.call_count == 2


def test_run_agent_rejects_invalid_ticket_id(monkeypatch):
    response = {
        "message": {
            "content": "",
            "tool_calls": [
                {
                    "function": {
                        "name": "get_ticket",
                        "arguments": {"ticket_id": -1},
                    }
                }
            ],
        }
    }

    fake_chat = Mock(return_value=response)
    monkeypatch.setattr(agent.ollama, "chat", fake_chat)

    fake_get_ticket = Mock(return_value=None)
    monkeypatch.setitem(
        agent.AVAILABLE_FUNCTIONS, "get_ticket", fake_get_ticket
    )

    try:
        agent.run_agent("Check ticket -1")
    except ValueError as error:
        assert str(error) == "ticket_id must be a positive integer."
    else:
        raise AssertionError("Expected ValueError")

    fake_get_ticket.assert_not_called()


def test_run_agent_rejects_unexpected_arguments(monkeypatch):
    response = {
        "message": {
            "content": "",
            "tool_calls": [
                {
                    "function": {
                        "name": "get_ticket",
                        "arguments": {
                            "ticket_id": 1,
                            "delete_database": True,
                        },
                    }
                }
            ],
        }
    }

    fake_chat = Mock(return_value=response)
    monkeypatch.setattr(agent.ollama, "chat", fake_chat)

    fake_get_ticket = Mock(return_value=None)
    monkeypatch.setitem(
        agent.AVAILABLE_FUNCTIONS, "get_ticket", fake_get_ticket
    )

    try:
        agent.run_agent("Check ticket 1")
    except ValueError as error:
        assert str(error) == "Unexpected arguments for get_ticket."
    else:
        raise AssertionError("Expected ValueError")

    fake_get_ticket.assert_not_called()


def test_run_agent_supports_multiple_tool_rounds(monkeypatch):
    first_response = {
        "message": {
            "content": "",
            "tool_calls": [
                {
                    "function": {
                        "name": "get_ticket",
                        "arguments": {"ticket_id": 1},
                    }
                }
            ],
        }
    }

    second_response = {
        "message": {
            "content": "",
            "tool_calls": [
                {
                    "function": {
                        "name": "get_ticket",
                        "arguments": {"ticket_id": 2},
                    }
                }
            ],
        }
    }

    final_response = {
        "message": {
            "content": "I checked both tickets.",
            "tool_calls": [],
        }
    }

    fake_chat = Mock(
        side_effect=[first_response, second_response, final_response]
    )
    monkeypatch.setattr(agent.ollama, "chat", fake_chat)

    fake_get_ticket = Mock(
        side_effect=[
            {"id": 1, "status": "open"},
            {"id": 2, "status": "closed"},
        ]
    )
    monkeypatch.setitem(
        agent.AVAILABLE_FUNCTIONS, "get_ticket", fake_get_ticket
    )

    result = agent.run_agent("Check tickets 1 and 2")

    assert result == "I checked both tickets."
    assert fake_chat.call_count == 3
    assert fake_get_ticket.call_count == 2


def test_run_agent_stops_after_maximum_tool_rounds(monkeypatch):
    response = {
        "message": {
            "content": "",
            "tool_calls": [
                {
                    "function": {
                        "name": "get_ticket",
                        "arguments": {"ticket_id": 1},
                    }
                }
            ],
        }
    }

    fake_chat = Mock(return_value=response)
    monkeypatch.setattr(agent.ollama, "chat", fake_chat)

    fake_get_ticket = Mock(return_value={"id": 1, "status": "open"})
    monkeypatch.setitem(
        agent.AVAILABLE_FUNCTIONS, "get_ticket", fake_get_ticket
    )

    try:
        agent.run_agent("Keep checking ticket 1")
    except RuntimeError as error:
        assert "maximum of 5 tool rounds" in str(error)
    else:
        raise AssertionError("Expected RuntimeError")

    assert fake_chat.call_count == agent.MAX_TOOL_ROUNDS + 1
    assert fake_get_ticket.call_count == agent.MAX_TOOL_ROUNDS


def test_run_agent_handles_tool_failure(monkeypatch):
    first_response = {
        "message": {
            "content": "",
            "tool_calls": [
                {
                    "function": {
                        "name": "get_ticket",
                        "arguments": {"ticket_id": 1},
                    }
                }
            ],
        }
    }

    final_response = {
        "message": {
            "content": "I couldn't retrieve that ticket because the tool failed.",
            "tool_calls": [],
        }
    }

    fake_chat = Mock(side_effect=[first_response, final_response])
    monkeypatch.setattr(agent.ollama, "chat", fake_chat)

    def failing_tool(ticket_id):
        raise RuntimeError("Sensitive internal database error")

    monkeypatch.setitem(
        agent.AVAILABLE_FUNCTIONS, "get_ticket", failing_tool
    )

    result = agent.run_agent("Check ticket 1")

    assert "couldn't retrieve" in result
    assert fake_chat.call_count == 2

    tool_messages = [
        message
        for message in fake_chat.call_args_list[1].kwargs["messages"]
        if message.get("role") == "tool"
    ]

    assert len(tool_messages) == 1

    tool_result = json.loads(tool_messages[0]["content"])

    assert tool_result["success"] is False
    assert "Sensitive internal database error" not in str(tool_result)

def test_request_ticket_closure_creates_pending_request():
    result = agent.request_ticket_closure(12)

    assert result["action"] == "close_ticket"
    assert result["ticket_id"] == 12
    assert result["status"] == "pending"
    assert result["request_id"]
    assert "approval" in result["message"].lower()


def test_request_ticket_closure_rejects_invalid_ticket_id():
    import pytest

    with pytest.raises(ValueError, match="positive integer"):
        agent.request_ticket_closure(0)
