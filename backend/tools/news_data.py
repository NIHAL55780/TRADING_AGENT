import os
from datetime import date, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

FINNHUB_COMPANY_NEWS_URL = "https://finnhub.io/api/v1/company-news"
MAX_ARTICLES = 10


def _get_api_key() -> str | None:
    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key or not api_key.strip():
        return None
    return api_key.strip()


def _normalize_ticker(ticker: str) -> str | None:
    if not ticker or not ticker.strip():
        return None
    return ticker.strip().upper()


def _format_article(raw: dict) -> dict:
    return {
        "headline": raw.get("headline") or "",
        "summary": raw.get("summary") or "",
        "url": raw.get("url") or "",
        "source": raw.get("source") or "",
        "datetime": int(raw["datetime"]) if raw.get("datetime") is not None else None,
    }


def get_news_data(ticker: str, days_back: int = 7) -> dict:
    symbol = _normalize_ticker(ticker)
    if not symbol:
        return {"error": "Ticker cannot be empty"}

    api_key = _get_api_key()
    if not api_key:
        return {"error": "FINNHUB_API_KEY environment variable is not set"}

    if days_back <= 0:
        return {"error": "days_back must be greater than 0"}

    try:
        today = date.today()
        from_date = today - timedelta(days=days_back)

        response = requests.get(
            FINNHUB_COMPANY_NEWS_URL,
            params={
                "symbol": symbol,
                "from": from_date.isoformat(),
                "to": today.isoformat(),
                "token": api_key,
            },
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        if not isinstance(data, list):
            if isinstance(data, dict) and data.get("error"):
                return {"error": str(data["error"])}
            return {"error": f"Unexpected news response for ticker '{symbol}'"}

        articles = [_format_article(item) for item in data if isinstance(item, dict)]
        articles.sort(key=lambda article: article.get("datetime") or 0, reverse=True)
        articles = articles[:MAX_ARTICLES]

        return {
            "ticker": symbol,
            "source": "Finnhub",
            "articles": articles,
            "article_count": len(articles),
        }
    except requests.RequestException as e:
        return {"error": f"Finnhub news request failed: {e}"}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    print(get_news_data("AAPL"))
