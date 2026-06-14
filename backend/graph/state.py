"""State definitions for LangGraph trading workflow."""

from typing import TypedDict


class TradingState(TypedDict):
    """State shared across trading workflow nodes.
    
    Attributes:
        ticker: Stock symbol (e.g., "AAPL")
        fundamental_report: Output from fundamental analysis agent
        technical_report: Output from technical analysis agent
        merged: Flag indicating if parallel reports have been merged
    """

    ticker: str
    fundamental_report: dict
    technical_report: dict
    merged: bool
