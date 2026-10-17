
import math

from embedding_service import generate_embedding


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot_product = sum(x * y for x, y in zip(a, b))

    magnitude_a = math.sqrt(sum(x * x for x in a))
    magnitude_b = math.sqrt(sum(y * y for y in b))

    if magnitude_a == 0 or magnitude_b == 0:
        raise ValueError("Embedding vectors must not be zero vectors.")

    return dot_product / (magnitude_a * magnitude_b)


if __name__ == "__main__":
    sentence_1 = (
        "Customers can reset their passwords through the account recovery page."
    )
    sentence_2 = (
        "I forgot my password and need to regain access to my account."
    )
    sentence_3 = "The weather is sunny and warm today."

    embedding_1 = generate_embedding(sentence_1)
    embedding_2 = generate_embedding(sentence_2)
    embedding_3 = generate_embedding(sentence_3)

    print(
        "Password sentences:",
        round(cosine_similarity(embedding_1, embedding_2), 4),
    )

    print(
        "Password vs weather:",
        round(cosine_similarity(embedding_1, embedding_3), 4),
    )
