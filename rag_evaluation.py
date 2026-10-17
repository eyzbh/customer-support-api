
from rag_service import answer_question


evaluation_questions = [
    {
        "question": "How do I reset my forgotten password?",
        "expected_source": "Password Recovery",
    },
    {
        "question": "Where can I review my invoices?",
        "expected_source": "Billing and Payments",
    },
    {
        "question": "What should I do if the application crashes?",
        "expected_source": "Technical Support",
    },
    {
        "question": "Does the company offer student discounts?",
        "expected_source": None,
    },
]


if __name__ == "__main__":
    for item in evaluation_questions:
        result = answer_question(item["question"])

        source_titles = [
            source["title"]
            for source in result["sources"]
        ]

        print("\nQuestion:", item["question"])
        print("Expected source:", item["expected_source"])
        print("Retrieved sources:", source_titles)
        print("Generated answer:", result["answer"])
