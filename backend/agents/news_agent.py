import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from tools.llm import ask_groq_json
from tools.news_data import get_news_data

AGENT_NAME = "News Analyst"
VALID_STANCES = {"Bullish", "Bearish", "Neutral"}


def _build_news_prompt(ticker: str, news_data: dict) -> str:
    articles = news_data.get("articles", [])
    return f"""
You are a News Analyst for a stock research platform.

Analyze recent company news using only the articles provided below.

Focus on:
- Recent events and announcements
- Positive or negative business developments
- Market-moving headlines

Return only valid JSON in this exact format:

{{
  "stance": "Bullish | Bearish | Neutral",
  "confidence": 0,
  "key_news": ["headline 1", "headline 2"],
  "reason": "Short explanation of the news impact"
}}

Rules:
- stance must be only one of: Bullish, Bearish, Neutral
- confidence must be a number between 0 and 100
- key_news must list only headlines from the provided articles
- Do not invent news that is not in the provided articles
- Base your analysis only on the provided data
- Do not include markdown
- Do not include extra text

Ticker: {ticker}

News Data:
{articles}
"""


def _neutral_response(
    ticker: str,
    reason: str,
    raw_data: dict,
    key_news: list[str] | None = None,
) -> dict:
    return {
        "agent": AGENT_NAME,
        "ticker": ticker,
        "stance": "Neutral",
        "confidence": 0,
        "key_news": key_news or [],
        "reason": reason,
        "raw_data": raw_data,
    }


def _normalize_llm_result(ticker: str, llm_result: dict, raw_data: dict) -> dict:
    if "error" in llm_result:
        return _neutral_response(
            ticker,
            "Could not analyze news because the LLM response was invalid.",
            raw_data,
        )

    stance = llm_result.get("stance", "Neutral")
    if stance not in VALID_STANCES:
        stance = "Neutral"

    confidence = llm_result.get("confidence", 0)
    try:
        confidence = max(0, min(100, int(confidence)))
    except (TypeError, ValueError):
        confidence = 0

    key_news = llm_result.get("key_news", [])
    if not isinstance(key_news, list):
        key_news = []
    key_news = [str(item) for item in key_news if item]

    reason = llm_result.get("reason") or "No explanation provided."

    return {
        "agent": AGENT_NAME,
        "ticker": ticker,
        "stance": stance,
        "confidence": confidence,
        "key_news": key_news,
        "reason": str(reason),
        "raw_data": raw_data,
    }


def run_news_agent(ticker: str) -> dict:
    if not ticker or not ticker.strip():
        return _neutral_response(
            "",
            "Could not analyze news because ticker is empty.",
            {"error": "Ticker cannot be empty"},
        )

    symbol = ticker.strip().upper()

    try:
        news_data = get_news_data(symbol)

        if "error" in news_data:
            return _neutral_response(
                symbol,
                "Could not analyze news because news data failed.",
                news_data,
            )

        if not news_data.get("articles"):
            return _neutral_response(
                symbol,
                "No recent news articles available for analysis.",
                news_data,
            )

        prompt = _build_news_prompt(symbol, news_data)
        llm_result = ask_groq_json(prompt)
        return _normalize_llm_result(symbol, llm_result, news_data)

    except Exception as e:
        return _neutral_response(
            symbol,
            "Could not analyze news because an unexpected error occurred.",
            {"error": str(e)},
        )


if __name__ == "__main__":
    print(run_news_agent("AAPL"))
