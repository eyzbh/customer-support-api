from transformers import pipeline

classifier = pipeline("sentiment-analysis")



def analyze_sentiment(text: str) -> dict:
    """Classify text as positive, neutral, or negative."""
    try:
        result = classifier(text)[0]

        return {
            "sentiment": result["label"],
            "score": round(result["score"], 4),
        }
    except Exception as exc:
        raise RuntimeError("Sentiment analysis failed.") from exc



if __name__ == "__main__":
    message = input("Enter a sentence to analyze: ")
    result = analyze_sentiment(message)

    print("\nSentiment Analysis Result")
    print("-------------------------")
    print(f"Text: {result['text']}")
    print(f"Sentiment: {result['sentiment']}")
    print(f"Confidence score: {result['score']}")
