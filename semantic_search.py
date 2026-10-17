
from embedding_service import generate_embedding
from compare_embeddings import cosine_similarity


knowledge_base = [
    {
        "title": "Password Recovery",
        "content": (
            "Customers can reset forgotten passwords through "
            "the account recovery page."
        ),
    },
    {
        "title": "Billing and Payments",
        "content": (
            "Customers can review invoices and payment history "
            "in the billing section of their account."
        ),
    },
    {
        "title": "Technical Support",
        "content": (
            "If the application crashes, restart it and check "
            "for available updates. Contact support if the issue continues."
        ),
    },
]


# Generate document embeddings once and reuse them.
indexed_knowledge_base = [
    {
        **document,
        "embedding": generate_embedding(document["content"]),
    }
    for document in knowledge_base
]



def search_knowledge_base(
    query: str,
    top_k: int = 2,
    min_score: float = 0.0,
) -> list[dict]:
    if not query.strip():
        raise ValueError("Search query must not be empty.")

    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    if not -1.0 <= min_score <= 1.0:
        raise ValueError("min_score must be between -1 and 1.")

    query_embedding = generate_embedding(query)

    results = []

    for document in indexed_knowledge_base:
        score = cosine_similarity(
            query_embedding,
            document["embedding"],
        )

        if score < min_score:
            continue

        results.append(
            {
                "title": document["title"],
                "content": document["content"],
                "score": score,
            }
        )

    return sorted(
        results,
        key=lambda item: item["score"],
        reverse=True,
    )[:top_k]




if __name__ == "__main__":
    queries = [
        "I forgot my password and cannot log in.",
        "Where can I see my invoices?",
        "My application keeps crashing.",
        "Does the company offer student discounts?",
        "What is the capital of Japan?",
    ]

    for query in queries:
        print(f"\nQuestion: {query}")

        results = search_knowledge_base(
            query,
            top_k=3,
            min_score=-1.0,
        )

        for result in results:
            print(
                f"  {result['title']}: "
                f"{result['score']:.4f}"
            )

