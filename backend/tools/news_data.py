def get_news_data(ticker: str) -> dict:
    if not ticker or not ticker.strip():
        return {"error": "Ticker cannot be empty"}

    symbol = ticker.strip().upper()

    try:
        return {
            "ticker": symbol,
            "articles": [],
            "message": "News API integration will be added later",
        }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    print(get_news_data("AAPL"))
