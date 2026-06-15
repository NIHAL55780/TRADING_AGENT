import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from tools.news_data import get_news_data


def _build_item_text(article: dict) -> str:
    headline = (article.get("headline") or "").strip()
    summary = (article.get("summary") or "").strip()

    if headline and summary:
        return f"{headline}. {summary}"
    return headline or summary


def get_sentiment_data(ticker: str) -> dict:
    if not ticker or not ticker.strip():
        return {"error": "Ticker cannot be empty"}

    symbol = ticker.strip().upper()

    try:
        news_data = get_news_data(symbol)

        if "error" in news_data:
            return {"error": news_data["error"]}

        articles = news_data.get("articles", [])
        items = []

        for article in articles:
            text = _build_item_text(article)
            if not text:
                continue

            items.append(
                {
                    "text": text,
                    "source": "news",
                }
            )

        return {
            "ticker": symbol,
            "source": "Finnhub News + Groq Sentiment",
            "items": items,
            "item_count": len(items),
        }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    print(get_sentiment_data("AAPL"))
