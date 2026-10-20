
import json

import ollama

from agent_tools import get_ticket


tools = [
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


messages = [
    {
        "role": "user",
        "content": "Look up support ticket 1 and tell me its status.",
    }
]

response = ollama.chat(
    model="qwen3:4b-instruct",
    messages=messages,
    tools=tools,
)

assistant_message = response["message"]
messages.append(assistant_message)

for tool_call in assistant_message.get("tool_calls") or []:
    tool_name = tool_call["function"]["name"]
    arguments = tool_call["function"]["arguments"]

    print(f"Executing tool: {tool_name}")
    print(f"Arguments: {arguments}")

    if tool_name == "get_ticket":
        result = get_ticket(**arguments)
    else:
        result = {"error": "Unknown tool"}

    messages.append(
        {
            "role": "tool",
            "tool_name": tool_name,
            "content": json.dumps(result),
        }
    )

    print(f"Tool result: {result}")

final_response = ollama.chat(
    model="qwen3:4b-instruct",
    messages=messages,
    tools=tools,
)

print("\nFinal answer:")
print(final_response["message"]["content"])
