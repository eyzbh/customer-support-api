
import json

import ollama

from agent_tools import get_ticket


MODEL_NAME = "qwen3:4b-instruct"
MAX_TOOL_ROUNDS = 5

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
    }
]

AVAILABLE_FUNCTIONS = {
    "get_ticket": get_ticket,
}



def run_agent(question: str) -> str:
    """Answer a question using registered tools with bounded execution."""

    if not question.strip():
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

        assistant_message = response["message"]
        tool_calls = assistant_message.get("tool_calls") or []

        if not tool_calls:
            return assistant_message["content"]

        # Allow at most MAX_TOOL_ROUNDS rounds of tool execution.
        # The final model call can answer, but cannot trigger more tools.
        if round_index == MAX_TOOL_ROUNDS:
            raise RuntimeError(
                f"Agent exceeded the maximum of {MAX_TOOL_ROUNDS} tool rounds."
            )

        messages.append(assistant_message)

        for tool_call in tool_calls:
            tool_name = tool_call["function"]["name"]
            arguments = tool_call["function"]["arguments"]

            function_to_call = AVAILABLE_FUNCTIONS.get(tool_name)

            if function_to_call is None:
                raise ValueError(
                    f"Unregistered tool requested: {tool_name}"
                )

            if tool_name == "get_ticket":
                if not isinstance(arguments, dict):
                    raise ValueError(
                        "Tool arguments must be a dictionary."
                    )

                ticket_id = arguments.get("ticket_id")

                if type(ticket_id) is not int or ticket_id < 1:
                    raise ValueError(
                        "ticket_id must be a positive integer."
                    )

                if set(arguments) != {"ticket_id"}:
                    raise ValueError(
                        "Unexpected arguments for get_ticket."
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
