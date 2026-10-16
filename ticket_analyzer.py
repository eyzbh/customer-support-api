from typing import Literal

import ollama
from pydantic import BaseModel, Field


class TicketAnalysis(BaseModel):
    category: Literal[
        "billing",
        "technical_support",
        "account_access",
        "other",
    ] = Field(
        description="The category of the customer's support issue."
    )

    priority: Literal["low", "medium", "high"] = Field(
        description="The urgency of the support issue."
    )

    suggested_reply: str = Field(
        description="A helpful reply to the customer."
    )


def analyze_ticket(message: str) -> TicketAnalysis:
    response = ollama.chat(
        model="qwen3:4b-instruct",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a customer support ticket analyzer. "
                    "Classify the customer's issue and suggest a helpful reply. "
                    "Choose a category such as billing, technical_support, "
                    "account_access, or other. "
                    "Priority must be low, medium, or high. "
                    "Never claim an action, such as a refund, has already "
                    "been completed unless the message confirms it."
                ),
            },
            {
                "role": "user",
                "content": message,
            },
        ],
        format=TicketAnalysis.model_json_schema(),
        options={"temperature": 0},
    )

    return TicketAnalysis.model_validate_json(
        response.message.content
    )
