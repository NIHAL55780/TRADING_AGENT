import sys
from pathlib import Path
from typing import Optional

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from tools.llm import ask_groq_json

AGENT_NAME = "Bull Researcher"


def _build_bull_prompt(
    ticker: str,
    fundamental_report: dict,
    technical_report: dict,
    news_report: Optional[dict] = None,
    sentiment_report: Optional[dict] = None,
) -> str:
    """Build the prompt for the bull researcher agent."""
    return f"""
You are a Bull Researcher Agent in a multi-agent stock research system.

Your job is to build the strongest possible BUY case for the stock using only the reports provided.

Focus on:
- Positive fundamentals
- Positive technical signals
- Positive news if available
- Positive market sentiment if available
- Growth opportunities
- Momentum
- Strengths that support buying

Return only valid JSON in this exact format:

{{
  "recommendation": "BUY",
  "confidence": 0,
  "arguments": [
    "First bullish argument",
    "Second bullish argument",
    "Third bullish argument"
  ],
  "summary": "Short bullish summary"
}}

Rules:
- recommendation must be exactly "BUY"
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


def _bull_neutral_response(ticker: str, reason: str, reports: dict) -> dict:
    """Return a neutral BUY response when analysis fails."""
    return {
        "agent": AGENT_NAME,
        "ticker": ticker,
        "recommendation": "BUY",
        "confidence": 0,
        "arguments": [
            "Insufficient data for analysis",
            reason,
        ],
        "summary": f"Bull researcher unable to provide complete analysis: {reason}",
        "input_reports": reports,
    }


def _normalize_bull_llm_result(
    ticker: str,
    llm_result: dict,
    reports: dict,
) -> dict:
    """Normalize LLM result and ensure valid format."""
    if "error" in llm_result:
        return _bull_neutral_response(
            ticker,
            "LLM response was invalid or malformed.",
            reports,
        )

    recommendation = llm_result.get("recommendation", "BUY")
    if recommendation not in ("BUY", "HOLD", "SELL"):
        recommendation = "BUY"

    confidence = llm_result.get("confidence", 0)
    try:
        confidence = max(0, min(100, int(confidence)))
    except (TypeError, ValueError):
        confidence = 0

    arguments = llm_result.get("arguments", [])
    if not isinstance(arguments, list):
        arguments = []
    arguments = [str(arg) for arg in arguments[:5]]

    summary = llm_result.get("summary") or "Bull case for the stock."

    return {
        "agent": AGENT_NAME,
        "ticker": ticker,
        "recommendation": recommendation,
        "confidence": confidence,
        "arguments": arguments,
        "summary": str(summary),
        "input_reports": reports,
    }


def run_bull_agent(
    ticker: str,
    fundamental_report: dict,
    technical_report: dict,
    news_report: Optional[dict] = None,
    sentiment_report: Optional[dict] = None,
) -> dict:
    """Run the Bull Researcher Agent.

    Args:
        ticker: Stock ticker symbol.
        fundamental_report: Output from fundamental analysis agent.
        technical_report: Output from technical analysis agent.
        news_report: Optional output from news analysis agent.
        sentiment_report: Optional output from sentiment analysis agent.

    Returns:
        Dict with recommendation (BUY), confidence, arguments, and summary.
    """
    # Validate ticker
    if not ticker or not ticker.strip():
        return _bull_neutral_response(
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
        prompt = _build_bull_prompt(
            symbol,
            fundamental_report,
            technical_report,
            news_report,
            sentiment_report,
        )
        llm_result = ask_groq_json(prompt)
        return _normalize_bull_llm_result(symbol, llm_result, reports)

    except Exception as e:
        return _bull_neutral_response(
            symbol,
            f"An unexpected error occurred: {str(e)}",
            reports,
        )


if __name__ == "__main__":
    # Test with dummy reports
    dummy_fundamental = {
        "agent": "Fundamental Analyst",
        "ticker": "TEST",
        "stance": "Bullish",
        "confidence": 75,
        "reason": "Strong revenue growth, low debt",
        "raw_data": {"revenue_growth": 15.5, "debt_to_equity": 0.5},
    }

    dummy_technical = {
        "agent": "Technical Analyst",
        "ticker": "TEST",
        "stance": "Bullish",
        "confidence": 70,
        "reason": "Price above 50-day MA, RSI bullish",
        "raw_data": {"rsi": 65, "price_above_sma50": True},
    }

    result = run_bull_agent(
        "TEST",
        dummy_fundamental,
        dummy_technical,
    )
    print(result)
