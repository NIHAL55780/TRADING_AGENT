import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from tools.llm import ask_groq_json
from tools.technical_indicators import get_technical_indicators

AGENT_NAME = "Technical Analyst"
VALID_STANCES = {"Bullish", "Bearish", "Neutral"}


def _build_technical_prompt(ticker: str, technical_data: dict) -> str:
    return f"""
You are a Technical Analyst for a stock research platform.

Analyze the stock's price trend, momentum, and volatility using the indicators below.

Focus only on:
- Trend direction
- Momentum
- Overbought or oversold conditions
- Volatility risk

Return only valid JSON in this exact format:

{{
  "stance": "Bullish | Bearish | Neutral",
  "confidence": 0,
  "reason": "Short explanation of the technical view"
}}

Rules:
- stance must be only one of: Bullish, Bearish, Neutral
- confidence must be a number between 0 and 100
- reason must be concise and based only on the provided data
- Do not include markdown
- Do not include extra text

Ticker: {ticker}

Technical Data:
{technical_data}
"""


def _neutral_response(ticker: str, reason: str, raw_data: dict) -> dict:
    return {
        "agent": AGENT_NAME,
        "ticker": ticker,
        "stance": "Neutral",
        "confidence": 0,
        "reason": reason,
        "raw_data": raw_data,
    }


def _normalize_llm_result(ticker: str, llm_result: dict, raw_data: dict) -> dict:
    if "error" in llm_result:
        return _neutral_response(
            ticker,
            "Could not analyze technicals because the LLM response was invalid.",
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
        "reason": str(reason),
        "raw_data": raw_data,
    }


def run_technical_agent(ticker: str) -> dict:
    if not ticker or not ticker.strip():
        return _neutral_response(
            "",
            "Could not analyze technicals because ticker is empty.",
            {"error": "Ticker cannot be empty"},
        )

    symbol = ticker.strip().upper()

    try:
        technical_data = get_technical_indicators(symbol)

        if "error" in technical_data:
            return _neutral_response(
                symbol,
                "Could not analyze technicals because technical data failed.",
                technical_data,
            )

        prompt = _build_technical_prompt(symbol, technical_data)
        llm_result = ask_groq_json(prompt)
        return _normalize_llm_result(symbol, llm_result, technical_data)

    except Exception as e:
        return _neutral_response(
            symbol,
            "Could not analyze technicals because an unexpected error occurred.",
            {"error": str(e)},
        )


if __name__ == "__main__":
    print(run_technical_agent("AAPL"))
