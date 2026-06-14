import sys
from pathlib import Path
from typing import Optional

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from tools.llm import ask_groq_json

AGENT_NAME = "Fund Manager"


def _build_fund_manager_prompt(
    ticker: str,
    trader_report: dict,
    risk_report: dict,
    fundamental_report: Optional[dict] = None,
    technical_report: Optional[dict] = None,
    bull_report: Optional[dict] = None,
    bear_report: Optional[dict] = None,
) -> str:
    """Build the prompt for the fund manager agent."""
    return f"""
You are the Fund Manager in a multi-agent stock research system.

Your job is to make the final research recommendation after reviewing:
- Trader decision
- Risk manager assessment
- Analyst reports
- Bull and bear debate

This is a research-only platform.
You must never approve real trade execution.

Choose exactly one final decision:
BUY, SELL, or HOLD

Return only valid JSON in this exact format:

{{
  "final_decision": "BUY | SELL | HOLD",
  "confidence": 0,
  "position_size": "0% | 1% | 3% | 5%",
  "execute": false,
  "reason": "Short final explanation"
}}

Rules:
- final_decision must be only BUY, SELL, or HOLD
- confidence must be 0 to 100
- execute must always be false
- Use the risk manager position_size
- If risk approval is false, prefer HOLD
- If trader confidence is low, prefer HOLD
- If risk is High, be conservative
- Base decision only on provided reports
- Do not invent facts
- Do not include markdown
- Do not include extra text

Ticker: {ticker}

Trader Report:
{trader_report}

Risk Report:
{risk_report}

Fundamental Report:
{fundamental_report}

Technical Report:
{technical_report}

Bull Report:
{bull_report}

Bear Report:
{bear_report}
"""


def _fund_manager_neutral_response(
    ticker: str,
    reason: str,
    reports: dict,
) -> dict:
    """Return a neutral HOLD response when analysis fails."""
    return {
        "agent": AGENT_NAME,
        "ticker": ticker,
        "final_decision": "HOLD",
        "confidence": 0,
        "position_size": "0%",
        "execute": False,
        "reason": f"Fund manager analysis failed: {reason}",
        "input_reports": reports,
    }


def _normalize_fund_manager_llm_result(
    ticker: str,
    llm_result: dict,
    reports: dict,
) -> dict:
    """Normalize LLM result and ensure valid format."""
    if "error" in llm_result:
        return _fund_manager_neutral_response(
            ticker,
            "LLM response was invalid or malformed.",
            reports,
        )

    final_decision = llm_result.get("final_decision", "HOLD")
    if final_decision not in ("BUY", "SELL", "HOLD"):
        final_decision = "HOLD"

    confidence = llm_result.get("confidence", 0)
    try:
        confidence = max(0, min(100, int(confidence)))
    except (TypeError, ValueError):
        confidence = 0

    position_size = llm_result.get("position_size", "0%")
    if position_size not in ("0%", "1%", "3%", "5%"):
        position_size = "0%"

    # execute must always be False
    execute = False

    reason = llm_result.get("reason") or "Final fund manager decision based on analysis."

    return {
        "agent": AGENT_NAME,
        "ticker": ticker,
        "final_decision": final_decision,
        "confidence": confidence,
        "position_size": position_size,
        "execute": execute,
        "reason": str(reason),
        "input_reports": reports,
    }


def run_fund_manager_agent(
    ticker: str,
    trader_report: dict,
    risk_report: dict,
    fundamental_report: Optional[dict] = None,
    technical_report: Optional[dict] = None,
    bull_report: Optional[dict] = None,
    bear_report: Optional[dict] = None,
) -> dict:
    """Run the Fund Manager Agent.

    Makes the final research recommendation after reviewing all reports.
    This is research-only; execute is always False.

    Args:
        ticker: Stock ticker symbol.
        trader_report: Output from trader agent.
        risk_report: Output from risk manager agent.
        fundamental_report: Optional output from fundamental analysis agent.
        technical_report: Optional output from technical analysis agent.
        bull_report: Optional output from bull researcher agent.
        bear_report: Optional output from bear researcher agent.

    Returns:
        Dict with final decision, confidence, position size, and execute flag.
    """
    # Validate ticker
    if not ticker or not ticker.strip():
        return _fund_manager_neutral_response(
            "",
            "Ticker cannot be empty.",
            {
                "trader_report": trader_report,
                "risk_report": risk_report,
                "fundamental_report": fundamental_report,
                "technical_report": technical_report,
                "bull_report": bull_report,
                "bear_report": bear_report,
            },
        )

    symbol = ticker.strip().upper()

    # Collect reports for reference
    reports = {
        "trader_report": trader_report,
        "risk_report": risk_report,
        "fundamental_report": fundamental_report,
        "technical_report": technical_report,
        "bull_report": bull_report,
        "bear_report": bear_report,
    }

    try:
        prompt = _build_fund_manager_prompt(
            symbol,
            trader_report,
            risk_report,
            fundamental_report,
            technical_report,
            bull_report,
            bear_report,
        )
        llm_result = ask_groq_json(prompt)
        return _normalize_fund_manager_llm_result(symbol, llm_result, reports)

    except Exception as e:
        return _fund_manager_neutral_response(
            symbol,
            f"An unexpected error occurred: {str(e)}",
            reports,
        )


if __name__ == "__main__":
    # Test with dummy reports
    dummy_trader = {
        "agent": "Trader",
        "ticker": "TEST",
        "decision": "BUY",
        "confidence": 75,
        "reason": "Strong case to buy",
        "bull_case_strength": 80,
        "bear_case_strength": 30,
    }

    dummy_risk = {
        "agent": "Risk Manager",
        "ticker": "TEST",
        "risk": "Low",
        "position_size": "5%",
        "approved": True,
        "reason": "Risk level is Low",
        "risk_factors": [],
    }

    dummy_fundamental = {
        "agent": "Fundamental Analyst",
        "ticker": "TEST",
        "stance": "Bullish",
        "confidence": 75,
    }

    dummy_technical = {
        "agent": "Technical Analyst",
        "ticker": "TEST",
        "stance": "Bullish",
        "confidence": 70,
    }

    dummy_bull = {
        "agent": "Bull Researcher",
        "ticker": "TEST",
        "recommendation": "BUY",
        "confidence": 80,
    }

    dummy_bear = {
        "agent": "Bear Researcher",
        "ticker": "TEST",
        "recommendation": "AVOID",
        "confidence": 30,
    }

    result = run_fund_manager_agent(
        "TEST",
        dummy_trader,
        dummy_risk,
        dummy_fundamental,
        dummy_technical,
        dummy_bull,
        dummy_bear,
    )
    print(result)
