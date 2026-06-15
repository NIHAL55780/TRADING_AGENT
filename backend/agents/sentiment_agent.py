import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from tools.llm import ask_groq_json
from tools.sentiment_data import get_sentiment_data

AGENT_NAME = "Sentiment Analyst"
VALID_STANCES = {"Bullish", "Bearish", "Neutral"}


def _build_sentiment_prompt(ticker: str, sentiment_data: dict) -> str:
    items = sentiment_data.get("items", [])
    return f"""
You are a Sentiment Analyst for a stock research platform.

Classify the overall market sentiment using only the text items provided below.

Each item is a news headline and summary. Do not invent social media sentiment or additional sources.

Return only valid JSON in this exact format:

{{
  "stance": "Bullish | Bearish | Neutral",
  "confidence": 0,
  "positive": 0,
  "negative": 0,
  "neutral": 0,
  "reason": "Short explanation of the overall sentiment"
}}

Rules:
- stance must be only one of: Bullish, Bearish, Neutral
- confidence must be a number between 0 and 100
- positive, negative, and neutral must be counts based only on the provided items
- positive + negative + neutral should equal the number of items analyzed
- Bullish means mostly positive sentiment
- Bearish means mostly negative sentiment
- Neutral means mixed or unclear sentiment
- Base your analysis only on the provided text items
- Do not invent social sentiment
- Do not include markdown
- Do not include extra text

Ticker: {ticker}

Sentiment Items:
{items}
"""


def _neutral_response(ticker: str, reason: str, raw_data: dict) -> dict:
    return {
        "agent": AGENT_NAME,
        "ticker": ticker,
        "stance": "Neutral",
        "confidence": 0,
        "positive": 0,
        "negative": 0,
        "neutral": 0,
        "reason": reason,
        "raw_data": raw_data,
    }


def _safe_count(value) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _normalize_llm_result(ticker: str, llm_result: dict, raw_data: dict) -> dict:
    if "error" in llm_result:
        return _neutral_response(
            ticker,
            "Could not analyze sentiment because the LLM response was invalid.",
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

    reason = llm_result.get("reason") or "No explanation provided."

    return {
        "agent": AGENT_NAME,
        "ticker": ticker,
        "stance": stance,
        "confidence": confidence,
        "positive": _safe_count(llm_result.get("positive")),
        "negative": _safe_count(llm_result.get("negative")),
        "neutral": _safe_count(llm_result.get("neutral")),
        "reason": str(reason),
        "raw_data": raw_data,
    }


def run_sentiment_agent(ticker: str) -> dict:
    if not ticker or not ticker.strip():
        return _neutral_response(
            "",
            "Could not analyze sentiment because ticker is empty.",
            {"error": "Ticker cannot be empty"},
        )

    symbol = ticker.strip().upper()

    try:
        sentiment_data = get_sentiment_data(symbol)

        if "error" in sentiment_data:
            return _neutral_response(
                symbol,
                "Could not analyze sentiment because sentiment data failed.",
                sentiment_data,
            )

        if not sentiment_data.get("items"):
            return _neutral_response(
                symbol,
                "No sentiment items available for analysis.",
                sentiment_data,
            )

        prompt = _build_sentiment_prompt(symbol, sentiment_data)
        llm_result = ask_groq_json(prompt)
        return _normalize_llm_result(symbol, llm_result, sentiment_data)

    except Exception as e:
        return _neutral_response(
            symbol,
            "Could not analyze sentiment because an unexpected error occurred.",
            {"error": str(e)},
        )


if __name__ == "__main__":
    print(run_sentiment_agent("AAPL"))
