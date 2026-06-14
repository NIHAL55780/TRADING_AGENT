def get_sentiment_data(ticker: str) -> dict:
    if not ticker or not ticker.strip():
        return {"error": "Ticker cannot be empty"}

    symbol = ticker.strip().upper()

    try:
        return {
            "ticker": symbol,
            "positive": 0,
            "negative": 0,
            "neutral": 0,
            "overall_sentiment": "Neutral",
            "message": "Sentiment API integration will be added later",
        }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    print(get_sentiment_data("AAPL"))
