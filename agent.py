
import json

import ollama

from agent_tools import get_ticket
from persistent_approval_service import create_approval_request


MODEL_NAME = "qwen3:4b-instruct"
MAX_TOOL_ROUNDS = 5


def request_ticket_closure(ticket_id: int) -> dict:
    """Request approval to close a ticket without changing its status."""

    request = create_approval_request(
        action="close_ticket",
        ticket_id=ticket_id,
        requested_by="ai-agent",
    )

    return {
        "request_id": (
            request["request_id"]
            if isinstance(request, dict)
            else request.request_id
        ),
        "action": (
            request["action"]
            if isinstance(request, dict)
            else request.action
        ),
        "ticket_id": (
            request["ticket_id"]
            if isinstance(request, dict)
            else request.ticket_id
        ),
        "status": (
            request["status"]
            if isinstance(request, dict)
            else request.status
        ),
        "message": (
            "Human approval is required before this ticket can be closed."
        ),
    }


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_ticket",
            "description": "Retrieve a support ticket by its ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "integer",
                        "description": "The ID of the support ticket.",
                    }
                },
                "required": ["ticket_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "request_ticket_closure",
            "description": (
                "Request human approval to close a support ticket. "
                "Creates a pending request but does not close the ticket."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "integer",
                        "description": "The ID of the ticket to close.",
                    }
                },
                "required": ["ticket_id"],
            },
        },
    },
]


AVAILABLE_FUNCTIONS = {
    "get_ticket": get_ticket,
    "request_ticket_closure": request_ticket_closure,
}


def run_agent(question: str) -> str:
    """Answer questions using registered tools with bounded execution."""

    if not isinstance(question, str) or not question.strip():
        raise ValueError("Question must not be empty.")

    messages = [
        {
            "role": "user",
            "content": question,
        }
    ]

    for round_index in range(MAX_TOOL_ROUNDS + 1):
        response = ollama.chat(
            model=MODEL_NAME,
            messages=messages,
            tools=TOOLS,
        )

        if not isinstance(response, dict):
            return "Sorry, I received an invalid response. Please try again."

        assistant_message = response.get("message")

        if not isinstance(assistant_message, dict):
            return "Sorry, I received an invalid response. Please try again."

        tool_calls = assistant_message.get("tool_calls") or []

        if not isinstance(tool_calls, list):
            raise ValueError("Tool calls must be a list.")

        if not tool_calls:
            content = assistant_message.get("content")

            if not isinstance(content, str):
                return (
                    "Sorry, I received an invalid response. Please try again."
                )

            return content

        # Allow at most MAX_TOOL_ROUNDS rounds of tool execution.
        if round_index == MAX_TOOL_ROUNDS:
            raise RuntimeError(
                f"Agent exceeded the maximum of {MAX_TOOL_ROUNDS} tool rounds."
            )

        messages.append(assistant_message)

        for tool_call in tool_calls:
            if not isinstance(tool_call, dict):
                raise ValueError("Tool call must be a dictionary.")

            function_data = tool_call.get("function")

            if not isinstance(function_data, dict):
                raise ValueError(
                    "Tool call function must be a dictionary."
                )

            tool_name = function_data.get("name")

            if not isinstance(tool_name, str) or not tool_name:
                raise ValueError(
                    "Tool call must include a valid function name."
                )

            if "arguments" not in function_data:
                raise ValueError("Tool call must include arguments.")

            arguments = function_data["arguments"]

            function_to_call = AVAILABLE_FUNCTIONS.get(tool_name)

            if function_to_call is None:
                raise ValueError(
                    f"Unregistered tool requested: {tool_name}"
                )

            if not isinstance(arguments, dict):
                raise ValueError("Tool arguments must be a dictionary.")

            if tool_name in {
                "get_ticket",
                "request_ticket_closure",
            }:
                ticket_id = arguments.get("ticket_id")

                if type(ticket_id) is not int or ticket_id < 1:
                    raise ValueError(
                        "ticket_id must be a positive integer."
                    )

                if set(arguments) != {"ticket_id"}:
                    raise ValueError(
                        f"Unexpected arguments for {tool_name}."
                    )

            try:
                result = function_to_call(**arguments)

                tool_result = {
                    "success": True,
                    "data": result,
                }

            except Exception:
                tool_result = {
                    "success": False,
                    "error": (
                        "The tool failed to execute. "
                        "No result is available."
                    ),
                }

            messages.append(
                {
                    "role": "tool",
                    "tool_name": tool_name,
                    "content": json.dumps(tool_result),
                }
            )

    raise RuntimeError(
        f"Agent exceeded the maximum of {MAX_TOOL_ROUNDS} tool rounds."
    )
