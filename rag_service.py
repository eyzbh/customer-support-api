
import ollama

from semantic_search import search_knowledge_base


def answer_question(question: str) -> dict:
    if not question.strip():
        raise ValueError("Question must not be empty.")

    sources = search_knowledge_base(
    question,
    top_k=2,
    min_score=0.60,
)
    if not sources:
      return {
        "question": question,
        "answer": (
            "I do not have enough information "
            "in the knowledge base to answer this question."
        ),
        "sources": [],
    }

    context = "\n\n".join(
        f"Source: {source['title']}\n"
        f"Content: {source['content']}"
        for source in sources
    )

    response = ollama.chat(
        model="qwen3:4b-instruct",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a customer-support assistant. "
                    "Answer using only the supplied knowledge sources. "
                    "If the sources do not contain enough information, "
                    "say you do not have enough information. "
                    "Do not invent policies, procedures, or facts."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Knowledge sources:\n{context}\n\n"
                    f"Customer question: {question}\n\n"
                    "Answer the question using the sources. "
                    "Be concise and include the titles of the sources used."
                ),
            },
        ],
    )

    return {
        "question": question,
        "answer": response["message"]["content"],
        "sources": [
            {
                "title": source["title"],
                "content": source["content"],
                "score": round(source["score"], 4),
            }
            for source in sources
        ],
    }
