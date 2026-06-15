import sys
from pathlib import Path
from typing import Optional

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

AGENT_NAME = "Risk Manager"


def classify_risk(
    rsi: Optional[float],
    volatility: Optional[float],
    trader_confidence: int,
) -> tuple[str, list[str]]:
    """Classify risk level based on technical indicators and trader confidence.

    Args:
        rsi: Relative Strength Index (0-100)
        volatility: Volatility as decimal (0.0-1.0)
        trader_confidence: Trader confidence (0-100)

    Returns:
        Tuple of (risk_level: str, risk_factors: list[str])
    """
    risk_factors = []

    # Default to Medium if data is missing
    if volatility is None or rsi is None or trader_confidence is None:
        return "Medium", ["Missing risk data, defaulting to Medium risk"]

    # High risk conditions
    if volatility >= 0.40:
        risk_factors.append("Volatility is high")

    if rsi >= 75:
        risk_factors.append("RSI indicates overbought conditions")

    if rsi <= 25:
        risk_factors.append("RSI indicates oversold conditions")

    if trader_confidence < 50:
        risk_factors.append("Trader confidence is low")

    if risk_factors:
        return "High", risk_factors

    # Medium risk conditions
    if volatility >= 0.25:
        risk_factors.append("Volatility is moderate")

    if rsi >= 70:
        risk_factors.append("RSI is near overbought levels")

    if rsi <= 30:
        risk_factors.append("RSI is near oversold levels")

    if trader_confidence < 65:
        risk_factors.append("Trader confidence is moderate")

    if risk_factors:
        return "Medium", risk_factors

    # Low risk
    return "Low", ["Risk indicators are within normal range"]


def determine_position_size(
    trader_decision: str,
    risk_level: str,
) -> str:
    """Determine position size based on decision and risk level.

    Args:
        trader_decision: BUY, SELL, or HOLD
        risk_level: Low, Medium, or High

    Returns:
        Position size as percentage string (e.g., "3%")
    """
    if trader_decision == "HOLD":
        return "0%"

    if risk_level == "High":
        return "1%"

    if risk_level == "Medium":
        return "3%"

    return "5%"


def determine_approval(
    trader_decision: str,
    risk_level: str,
) -> bool:
    """Determine if position is approved for execution.

    Args:
        trader_decision: BUY, SELL, or HOLD
        risk_level: Low, Medium, or High

    Returns:
        True if position is approved, False otherwise
    """
    if trader_decision == "HOLD":
        return False

    if trader_decision == "SELL":
        return False

    # For BUY decisions: approve if risk is not High
    if risk_level == "High":
        return True  # Approve but with minimal position

    return True


def run_risk_manager_agent(
    ticker: str,
    trader_report: dict,
    technical_report: dict,
) -> dict:
    """Run the Risk Manager Agent.

    Assesses risk and determines position size using rule-based logic.

    Args:
        ticker: Stock ticker symbol.
        trader_report: Output from trader agent.
        technical_report: Output from technical analysis agent.

    Returns:
        Dict with risk assessment, position size, and approval status.
    """
    # Validate ticker
    if not ticker or not ticker.strip():
        return {
            "agent": AGENT_NAME,
            "ticker": "",
            "risk": "Medium",
            "position_size": "0%",
            "approved": False,
            "reason": "Ticker cannot be empty.",
            "risk_factors": ["Invalid ticker"],
        }

    symbol = ticker.strip().upper()

    try:
        # Extract trader decision and confidence
        trader_decision = trader_report.get("decision", "HOLD")
        trader_confidence = trader_report.get("confidence", 50)

        # Extract technical indicators
        raw_data = technical_report.get("raw_data", {})
        rsi = raw_data.get("rsi_14")
        volatility = raw_data.get("volatility")

        # Classify risk
        risk_level, risk_factors = classify_risk(rsi, volatility, trader_confidence)

        # Determine position size
        position_size = determine_position_size(trader_decision, risk_level)

        # Determine approval
        approved = determine_approval(trader_decision, risk_level)

        # Build reason
        reason = f"Risk level is {risk_level}. Position size: {position_size}."
        if not approved:
            reason += " Position not approved for execution."

        return {
            "agent": AGENT_NAME,
            "ticker": symbol,
            "risk": risk_level,
            "position_size": position_size,
            "approved": approved,
            "reason": reason,
            "risk_factors": risk_factors,
        }

    except Exception as e:
        return {
            "agent": AGENT_NAME,
            "ticker": symbol,
            "risk": "Medium",
            "position_size": "0%",
            "approved": False,
            "reason": f"Risk assessment failed: {str(e)}",
            "risk_factors": ["Analysis error"],
        }


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

    dummy_technical = {
        "agent": "Technical Analyst",
        "ticker": "TEST",
        "stance": "Bullish",
        "confidence": 70,
        "reason": "Price above 50-day MA",
        "raw_data": {
            "rsi_14": 65,
            "volatility": 0.22,
        },
    }

    result = run_risk_manager_agent(
        "TEST",
        dummy_trader,
        dummy_technical,
    )
    print(result)
