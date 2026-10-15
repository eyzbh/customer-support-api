from transformers import pipeline

classifier = pipeline(
    "sentiment-analysis",
    model="cardiffnlp/twitter-roberta-base-sentiment-latest",
)


def analyze_sentiment(text: str) -> dict:
    """Classify text as positive, neutral, or negative."""
    result = classifier(text)[0]

    return {
        "sentiment": result["label"],
        "score": round(result["score"], 4),
    }
