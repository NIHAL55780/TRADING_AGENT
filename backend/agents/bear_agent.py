import sys
from pathlib import Path
from typing import Optional

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from tools.llm import ask_groq_json

AGENT_NAME = "Bear Researcher"


def _build_bear_prompt(
    ticker: str,
    fundamental_report: dict,
    technical_report: dict,
    news_report: Optional[dict] = None,
    sentiment_report: Optional[dict] = None,
) -> str:
    """Build the prompt for the bear researcher agent."""
    return f"""
You are a Bear Researcher Agent in a multi-agent stock research system.

Your job is to build the strongest possible case AGAINST buying the stock using only the reports provided.

Focus on:
- Weak fundamentals
- High debt or valuation risk
- Negative technical signals
- Overbought conditions
- Negative news if available
- Negative market sentiment if available
- Downside risk
- Uncertainty

Return only valid JSON in this exact format:

{{
  "recommendation": "AVOID",
  "confidence": 0,
  "arguments": [
    "First bearish argument",
    "Second bearish argument",
    "Third bearish argument"
  ],
  "summary": "Short bearish summary"
}}

Rules:
- recommendation must be exactly "AVOID"
- confidence must be a number from 0 to 100
- arguments must contain 3 to 5 concise points
- Base arguments only on provided reports
- Do not invent financial facts
- Do not include markdown
- Do not include extra text

Ticker: {ticker}

Fundamental Report:
{fundamental_report}

Technical Report:
{technical_report}

News Report:
{news_report}

Sentiment Report:
{sentiment_report}
"""


def _bear_neutral_response(ticker: str, reason: str, reports: dict) -> dict:
    """Return a neutral AVOID response when analysis fails."""
    return {
        "agent": AGENT_NAME,
        "ticker": ticker,
        "recommendation": "AVOID",
        "confidence": 0,
        "arguments": [
            "Insufficient data for analysis",
            reason,
        ],
        "summary": f"Bear researcher unable to provide complete analysis: {reason}",
        "input_reports": reports,
    }


def _normalize_bear_llm_result(
    ticker: str,
    llm_result: dict,
    reports: dict,
) -> dict:
    """Normalize LLM result and ensure valid format."""
    if "error" in llm_result:
        return _bear_neutral_response(
            ticker,
            "LLM response was invalid or malformed.",
            reports,
        )

    recommendation = llm_result.get("recommendation", "AVOID")
    if recommendation not in ("BUY", "HOLD", "SELL", "AVOID"):
        recommendation = "AVOID"

    confidence = llm_result.get("confidence", 0)
    try:
        confidence = max(0, min(100, int(confidence)))
    except (TypeError, ValueError):
        confidence = 0

    arguments = llm_result.get("arguments", [])
    if not isinstance(arguments, list):
        arguments = []
    arguments = [str(arg) for arg in arguments[:5]]

    summary = llm_result.get("summary") or "Bear case against the stock."

    return {
        "agent": AGENT_NAME,
        "ticker": ticker,
        "recommendation": recommendation,
        "confidence": confidence,
        "arguments": arguments,
        "summary": str(summary),
        "input_reports": reports,
    }


def run_bear_agent(
    ticker: str,
    fundamental_report: dict,
    technical_report: dict,
    news_report: Optional[dict] = None,
    sentiment_report: Optional[dict] = None,
) -> dict:
    """Run the Bear Researcher Agent.

    Args:
        ticker: Stock ticker symbol.
        fundamental_report: Output from fundamental analysis agent.
        technical_report: Output from technical analysis agent.
        news_report: Optional output from news analysis agent.
        sentiment_report: Optional output from sentiment analysis agent.

    Returns:
        Dict with recommendation (SELL), confidence, arguments, and summary.
    """
    # Validate ticker
    if not ticker or not ticker.strip():
        return _bear_neutral_response(
            "",
            "Ticker cannot be empty.",
            {
                "fundamental_report": fundamental_report,
                "technical_report": technical_report,
                "news_report": news_report,
                "sentiment_report": sentiment_report,
            },
        )

    symbol = ticker.strip().upper()

    # Collect reports for reference
    reports = {
        "fundamental_report": fundamental_report,
        "technical_report": technical_report,
        "news_report": news_report,
        "sentiment_report": sentiment_report,
    }

    try:
        prompt = _build_bear_prompt(
            symbol,
            fundamental_report,
            technical_report,
            news_report,
            sentiment_report,
        )
        llm_result = ask_groq_json(prompt)
        return _normalize_bear_llm_result(symbol, llm_result, reports)

    except Exception as e:
        return _bear_neutral_response(
            symbol,
            f"An unexpected error occurred: {str(e)}",
            reports,
        )


if __name__ == "__main__":
    # Test with dummy reports
    dummy_fundamental = {
        "agent": "Fundamental Analyst",
        "ticker": "TEST",
        "stance": "Bearish",
        "confidence": 75,
        "reason": "High debt, declining margins",
        "raw_data": {"revenue_growth": -5.2, "debt_to_equity": 2.3},
    }

    dummy_technical = {
        "agent": "Technical Analyst",
        "ticker": "TEST",
        "stance": "Bearish",
        "confidence": 70,
        "reason": "Price below 50-day MA, RSI bearish",
        "raw_data": {"rsi": 35, "price_above_sma50": False},
    }

    result = run_bear_agent(
        "TEST",
        dummy_fundamental,
        dummy_technical,
    )
    print(result)
