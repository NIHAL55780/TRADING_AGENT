"""State definitions for LangGraph trading workflow."""

from typing import TypedDict


class TradingState(TypedDict):
    """State shared across the multi-agent trading workflow."""

    ticker: str

    fundamental_report: dict
    technical_report: dict
    news_report: dict
    sentiment_report: dict

    analysts_merged: bool

    bull_report: dict
    bear_report: dict

    research_merged: bool

    trader_report: dict
    risk_report: dict
    fund_manager_report: dict

    final_decision: str
