import sys
from pathlib import Path
from typing import Optional

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from tools.llm import ask_groq_json

AGENT_NAME = "Trader"


def _build_trader_prompt(
    ticker: str,
    fundamental_report: dict,
    technical_report: dict,
    bull_report: dict,
    bear_report: dict,
    news_report: Optional[dict] = None,
    sentiment_report: Optional[dict] = None,
) -> str:
    """Build the prompt for the trader agent."""
    return f"""
You are the Lead Trader in a multi-agent stock research system.

Your job is to make a final research decision using all available reports.

You must compare:
- Bullish evidence
- Bearish evidence
- Fundamental strength
- Technical trend
- News and sentiment if available

Choose exactly one decision:
BUY, SELL, or HOLD

Return only valid JSON in this exact format:

{{
  "decision": "BUY | SELL | HOLD",
  "confidence": 0,
  "reason": "Short explanation",
  "bull_case_strength": 0,
  "bear_case_strength": 0
}}

Rules:
- decision must be only BUY, SELL, or HOLD
- confidence must be 0 to 100
- bull_case_strength must be 0 to 100
- bear_case_strength must be 0 to 100
- Base your decision only on provided reports
- Do not invent facts
- Do not include markdown
- Do not include extra text
- This is research only, not real trading execution

Ticker: {ticker}

Fundamental Report:
{fundamental_report}

Technical Report:
{technical_report}

Bull Report:
{bull_report}

Bear Report:
{bear_report}

News Report:
{news_report}

Sentiment Report:
{sentiment_report}
"""


def _trader_neutral_response(ticker: str, reason: str, reports: dict) -> dict:
    """Return a neutral HOLD response when analysis fails."""
    return {
        "agent": AGENT_NAME,
        "ticker": ticker,
        "decision": "HOLD",
        "confidence": 0,
        "reason": f"Trader unable to make decision: {reason}",
        "bull_case_strength": 0,
        "bear_case_strength": 0,
        "input_reports": reports,
    }


def _normalize_trader_llm_result(
    ticker: str,
    llm_result: dict,
    reports: dict,
) -> dict:
    """Normalize LLM result and ensure valid format."""
    if "error" in llm_result:
        return _trader_neutral_response(
            ticker,
            "LLM response was invalid or malformed.",
            reports,
        )

    decision = llm_result.get("decision", "HOLD")
    if decision not in ("BUY", "SELL", "HOLD"):
        decision = "HOLD"

    confidence = llm_result.get("confidence", 0)
    try:
        confidence = max(0, min(100, int(confidence)))
    except (TypeError, ValueError):
        confidence = 0

    bull_strength = llm_result.get("bull_case_strength", 0)
    try:
        bull_strength = max(0, min(100, int(bull_strength)))
    except (TypeError, ValueError):
        bull_strength = 0

    bear_strength = llm_result.get("bear_case_strength", 0)
    try:
        bear_strength = max(0, min(100, int(bear_strength)))
    except (TypeError, ValueError):
        bear_strength = 0

    reason = llm_result.get("reason") or "Trader decision based on analysis."

    return {
        "agent": AGENT_NAME,
        "ticker": ticker,
        "decision": decision,
        "confidence": confidence,
        "reason": str(reason),
        "bull_case_strength": bull_strength,
        "bear_case_strength": bear_strength,
        "input_reports": reports,
    }


def run_trader_agent(
    ticker: str,
    fundamental_report: dict,
    technical_report: dict,
    bull_report: dict,
    bear_report: dict,
    news_report: Optional[dict] = None,
    sentiment_report: Optional[dict] = None,
) -> dict:
    """Run the Trader Agent.

    Makes BUY / SELL / HOLD decision based on all available reports.

    Args:
        ticker: Stock ticker symbol.
        fundamental_report: Output from fundamental analysis agent.
        technical_report: Output from technical analysis agent.
        bull_report: Output from bull researcher agent.
        bear_report: Output from bear researcher agent.
        news_report: Optional output from news analysis agent.
        sentiment_report: Optional output from sentiment analysis agent.

    Returns:
        Dict with BUY/SELL/HOLD decision, confidence, and strength assessments.
    """
    # Validate ticker
    if not ticker or not ticker.strip():
        return _trader_neutral_response(
            "",
            "Ticker cannot be empty.",
            {
                "fundamental_report": fundamental_report,
                "technical_report": technical_report,
                "bull_report": bull_report,
                "bear_report": bear_report,
                "news_report": news_report,
                "sentiment_report": sentiment_report,
            },
        )

    symbol = ticker.strip().upper()

    # Collect reports for reference
    reports = {
        "fundamental_report": fundamental_report,
        "technical_report": technical_report,
        "bull_report": bull_report,
        "bear_report": bear_report,
        "news_report": news_report,
        "sentiment_report": sentiment_report,
    }

    try:
        prompt = _build_trader_prompt(
            symbol,
            fundamental_report,
            technical_report,
            bull_report,
            bear_report,
            news_report,
            sentiment_report,
        )
        llm_result = ask_groq_json(prompt)
        return _normalize_trader_llm_result(symbol, llm_result, reports)

    except Exception as e:
        return _trader_neutral_response(
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
    }

    dummy_technical = {
        "agent": "Technical Analyst",
        "ticker": "TEST",
        "stance": "Bullish",
        "confidence": 70,
        "reason": "Price above 50-day MA",
    }

    dummy_bull = {
        "agent": "Bull Researcher",
        "ticker": "TEST",
        "recommendation": "BUY",
        "confidence": 80,
        "arguments": ["Growing revenue", "Strong margins"],
        "summary": "Strong buy case",
    }

    dummy_bear = {
        "agent": "Bear Researcher",
        "ticker": "TEST",
        "recommendation": "AVOID",
        "confidence": 40,
        "arguments": ["Some valuation risk"],
        "summary": "Moderate risks",
    }

    result = run_trader_agent(
        "TEST",
        dummy_fundamental,
        dummy_technical,
        dummy_bull,
        dummy_bear,
    )
    print(result)
