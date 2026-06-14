"""LangGraph workflow for coordinating fundamental and technical agents."""

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from typing import Any

from langgraph.graph import END, START, StateGraph

from agents.fundamental_agent import run_fundamental_agent
from agents.technical_agent import run_technical_agent
from graph.state import TradingState


def fundamental_node(state: TradingState) -> dict[str, Any]:
    """Run fundamental analysis on the ticker.
    
    Returns only the fundamental_report key to avoid concurrent state conflicts.
    """
    ticker = state.get("ticker", "").strip()

    if not ticker:
        return {"fundamental_report": {"error": "Ticker is empty"}}

    try:
        report = run_fundamental_agent(ticker)
        return {"fundamental_report": report}
    except Exception as e:
        return {"fundamental_report": {"error": f"Fundamental analysis failed: {str(e)}"}}


def technical_node(state: TradingState) -> dict[str, Any]:
    """Run technical analysis on the ticker.
    
    Returns only the technical_report key to avoid concurrent state conflicts.
    """
    ticker = state.get("ticker", "").strip()

    if not ticker:
        return {"technical_report": {"error": "Ticker is empty"}}

    try:
        report = run_technical_agent(ticker)
        return {"technical_report": report}
    except Exception as e:
        return {"technical_report": {"error": f"Technical analysis failed: {str(e)}"}}


def merge_node(state: TradingState) -> dict[str, Any]:
    """Merge the outputs from both parallel agents.
    
    Ensures both fundamental and technical reports are available.
    Returns only the merged key to maintain clean state updates.
    """
    fundamental = state.get("fundamental_report", {})
    technical = state.get("technical_report", {})

    # Check for errors in either report
    if "error" in fundamental or "error" in technical:
        return {
            "merged": False,
        }

    # Both reports completed successfully
    return {
        "merged": True,
    }


def build_trading_graph() -> StateGraph:
    """Build and compile the parallel trading workflow graph.

    Workflow:
         START
           ├── fundamental_node
           └── technical_node
                 ↓
            merge_node
                 ↓
                END

    Returns:
        Compiled StateGraph for the trading workflow.
    """
    graph = StateGraph(TradingState)

    # Add nodes
    graph.add_node("fundamental_node", fundamental_node)
    graph.add_node("technical_node", technical_node)
    graph.add_node("merge_node", merge_node)

    # Add edges for parallel execution
    # Both nodes start immediately after START
    graph.add_edge(START, "fundamental_node")
    graph.add_edge(START, "technical_node")

    # Both nodes converge at merge_node
    graph.add_edge("fundamental_node", "merge_node")
    graph.add_edge("technical_node", "merge_node")

    # Merge node leads to END
    graph.add_edge("merge_node", END)

    return graph.compile()


def run_trading_workflow(ticker: str) -> dict:
    """Run the trading workflow for a given ticker.

    Executes fundamental and technical analysis in parallel, then merges results.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL", "MSFT")

    Returns:
        Final state dict containing:
        - ticker: The stock symbol (uppercase)
        - fundamental_report: Output from fundamental agent
        - technical_report: Output from technical agent
        - merged: Whether merge was successful
    """
    # Validate ticker
    if not ticker or not ticker.strip():
        return {
            "ticker": "",
            "fundamental_report": {"error": "Ticker cannot be empty"},
            "technical_report": {"error": "Ticker cannot be empty"},
            "merged": False,
        }

    # Create initial state
    initial_state = {
        "ticker": ticker.upper().strip(),
        "fundamental_report": {},
        "technical_report": {},
        "merged": False,
    }

    try:
        # Build and run the graph
        graph = build_trading_graph()
        final_state = graph.invoke(initial_state)
        return final_state
    except Exception as e:
        return {
            "ticker": ticker.upper().strip(),
            "fundamental_report": {"error": f"Workflow failed: {str(e)}"},
            "technical_report": {"error": f"Workflow failed: {str(e)}"},
            "merged": False,
        }


if __name__ == "__main__":
    result = run_trading_workflow("AAPL")
    print(result)

