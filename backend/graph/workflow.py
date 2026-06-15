"""LangGraph workflow for the complete multi-agent trading system."""

import sys
from pathlib import Path
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from langgraph.graph import END, START, StateGraph

from agents.bear_agent import run_bear_agent
from agents.bull_agent import run_bull_agent
from agents.fund_manager_agent import run_fund_manager_agent
from agents.fundamental_agent import run_fundamental_agent
from agents.news_agent import run_news_agent
from agents.risk_manager_agent import run_risk_manager_agent
from agents.sentiment_agent import run_sentiment_agent
from agents.technical_agent import run_technical_agent
from agents.trader_agent import run_trader_agent
from graph.state import TradingState


def _get_ticker(state: TradingState) -> str:
    return state.get("ticker", "").strip().upper()


def _fundamental_fallback(ticker: str, reason: str) -> dict:
    return {
        "agent": "Fundamental Analyst",
        "ticker": ticker,
        "stance": "Neutral",
        "confidence": 0,
        "reason": f"Fundamental agent failed: {reason}",
    }


def _technical_fallback(ticker: str, reason: str) -> dict:
    return {
        "agent": "Technical Analyst",
        "ticker": ticker,
        "stance": "Neutral",
        "confidence": 0,
        "reason": f"Technical agent failed: {reason}",
    }


def _news_fallback(ticker: str, reason: str) -> dict:
    return {
        "agent": "News Analyst",
        "ticker": ticker,
        "stance": "Neutral",
        "confidence": 0,
        "key_news": [],
        "reason": f"News agent failed: {reason}",
    }


def _sentiment_fallback(ticker: str, reason: str) -> dict:
    return {
        "agent": "Sentiment Analyst",
        "ticker": ticker,
        "stance": "Neutral",
        "confidence": 0,
        "positive": 0,
        "negative": 0,
        "neutral": 0,
        "reason": f"Sentiment agent failed: {reason}",
    }


def _bull_fallback(ticker: str, reason: str) -> dict:
    return {
        "agent": "Bull Researcher",
        "ticker": ticker,
        "recommendation": "BUY",
        "confidence": 0,
        "arguments": [],
        "summary": f"Bull agent failed: {reason}",
    }


def _bear_fallback(ticker: str, reason: str) -> dict:
    return {
        "agent": "Bear Researcher",
        "ticker": ticker,
        "recommendation": "AVOID",
        "confidence": 0,
        "arguments": [],
        "summary": f"Bear agent failed: {reason}",
    }


def _trader_fallback(ticker: str, reason: str) -> dict:
    return {
        "agent": "Trader",
        "ticker": ticker,
        "decision": "HOLD",
        "confidence": 0,
        "reason": f"Trader agent failed: {reason}",
        "bull_case_strength": 0,
        "bear_case_strength": 0,
    }


def _risk_fallback(ticker: str, reason: str) -> dict:
    return {
        "agent": "Risk Manager",
        "ticker": ticker,
        "risk": "Medium",
        "position_size": "0%",
        "approved": False,
        "reason": f"Risk manager failed: {reason}",
        "risk_factors": [],
    }


def _fund_manager_fallback(ticker: str, reason: str) -> dict:
    return {
        "agent": "Fund Manager",
        "ticker": ticker,
        "final_decision": "HOLD",
        "confidence": 0,
        "position_size": "0%",
        "execute": False,
        "reason": f"Fund manager failed: {reason}",
    }


def fundamental_node(state: TradingState) -> dict[str, Any]:
    ticker = _get_ticker(state)
    if not ticker:
        return {"fundamental_report": _fundamental_fallback("", "Ticker is empty")}

    try:
        return {"fundamental_report": run_fundamental_agent(ticker)}
    except Exception as e:
        return {"fundamental_report": _fundamental_fallback(ticker, str(e))}


def technical_node(state: TradingState) -> dict[str, Any]:
    ticker = _get_ticker(state)
    if not ticker:
        return {"technical_report": _technical_fallback("", "Ticker is empty")}

    try:
        return {"technical_report": run_technical_agent(ticker)}
    except Exception as e:
        return {"technical_report": _technical_fallback(ticker, str(e))}


def news_node(state: TradingState) -> dict[str, Any]:
    ticker = _get_ticker(state)
    if not ticker:
        return {"news_report": _news_fallback("", "Ticker is empty")}

    try:
        return {"news_report": run_news_agent(ticker)}
    except Exception as e:
        return {"news_report": _news_fallback(ticker, str(e))}


def sentiment_node(state: TradingState) -> dict[str, Any]:
    ticker = _get_ticker(state)
    if not ticker:
        return {"sentiment_report": _sentiment_fallback("", "Ticker is empty")}

    try:
        return {"sentiment_report": run_sentiment_agent(ticker)}
    except Exception as e:
        return {"sentiment_report": _sentiment_fallback(ticker, str(e))}


def merge_analyst_node(state: TradingState) -> dict[str, Any]:
    return {"analysts_merged": True}


def bull_node(state: TradingState) -> dict[str, Any]:
    ticker = _get_ticker(state)
    if not ticker:
        return {"bull_report": _bull_fallback("", "Ticker is empty")}

    try:
        report = run_bull_agent(
            ticker,
            state.get("fundamental_report", {}),
            state.get("technical_report", {}),
            state.get("news_report", {}),
            state.get("sentiment_report", {}),
        )
        return {"bull_report": report}
    except Exception as e:
        return {"bull_report": _bull_fallback(ticker, str(e))}


def bear_node(state: TradingState) -> dict[str, Any]:
    ticker = _get_ticker(state)
    if not ticker:
        return {"bear_report": _bear_fallback("", "Ticker is empty")}

    try:
        report = run_bear_agent(
            ticker,
            state.get("fundamental_report", {}),
            state.get("technical_report", {}),
            state.get("news_report", {}),
            state.get("sentiment_report", {}),
        )
        return {"bear_report": report}
    except Exception as e:
        return {"bear_report": _bear_fallback(ticker, str(e))}


def merge_research_node(state: TradingState) -> dict[str, Any]:
    return {"research_merged": True}


def trader_node(state: TradingState) -> dict[str, Any]:
    ticker = _get_ticker(state)
    if not ticker:
        return {"trader_report": _trader_fallback("", "Ticker is empty")}

    try:
        report = run_trader_agent(
            ticker,
            state.get("fundamental_report", {}),
            state.get("technical_report", {}),
            state.get("bull_report", {}),
            state.get("bear_report", {}),
            state.get("news_report", {}),
            state.get("sentiment_report", {}),
        )
        return {"trader_report": report}
    except Exception as e:
        return {"trader_report": _trader_fallback(ticker, str(e))}


def risk_node(state: TradingState) -> dict[str, Any]:
    ticker = _get_ticker(state)
    if not ticker:
        return {"risk_report": _risk_fallback("", "Ticker is empty")}

    try:
        report = run_risk_manager_agent(
            ticker,
            state.get("trader_report", {}),
            state.get("technical_report", {}),
        )
        return {"risk_report": report}
    except Exception as e:
        return {"risk_report": _risk_fallback(ticker, str(e))}


def fund_manager_node(state: TradingState) -> dict[str, Any]:
    ticker = _get_ticker(state)
    if not ticker:
        report = _fund_manager_fallback("", "Ticker is empty")
        return {
            "fund_manager_report": report,
            "final_decision": report["final_decision"],
        }

    try:
        report = run_fund_manager_agent(
            ticker,
            state.get("trader_report", {}),
            state.get("risk_report", {}),
            state.get("fundamental_report", {}),
            state.get("technical_report", {}),
            state.get("bull_report", {}),
            state.get("bear_report", {}),
        )
        final_decision = report.get("final_decision", "HOLD")
        return {
            "fund_manager_report": report,
            "final_decision": final_decision,
        }
    except Exception as e:
        report = _fund_manager_fallback(ticker, str(e))
        return {
            "fund_manager_report": report,
            "final_decision": report["final_decision"],
        }


def build_trading_graph():
    """Build and compile the complete multi-agent trading workflow graph."""
    graph = StateGraph(TradingState)

    graph.add_node("fundamental_node", fundamental_node)
    graph.add_node("technical_node", technical_node)
    graph.add_node("news_node", news_node)
    graph.add_node("sentiment_node", sentiment_node)
    graph.add_node("merge_analyst_node", merge_analyst_node)
    graph.add_node("bull_node", bull_node)
    graph.add_node("bear_node", bear_node)
    graph.add_node("merge_research_node", merge_research_node)
    graph.add_node("trader_node", trader_node)
    graph.add_node("risk_node", risk_node)
    graph.add_node("fund_manager_node", fund_manager_node)

    graph.add_edge(START, "fundamental_node")
    graph.add_edge(START, "technical_node")
    graph.add_edge(START, "news_node")
    graph.add_edge(START, "sentiment_node")

    graph.add_edge("fundamental_node", "merge_analyst_node")
    graph.add_edge("technical_node", "merge_analyst_node")
    graph.add_edge("news_node", "merge_analyst_node")
    graph.add_edge("sentiment_node", "merge_analyst_node")

    graph.add_edge("merge_analyst_node", "bull_node")
    graph.add_edge("merge_analyst_node", "bear_node")

    graph.add_edge("bull_node", "merge_research_node")
    graph.add_edge("bear_node", "merge_research_node")

    graph.add_edge("merge_research_node", "trader_node")
    graph.add_edge("trader_node", "risk_node")
    graph.add_edge("risk_node", "fund_manager_node")
    graph.add_edge("fund_manager_node", END)

    return graph.compile()


def _initial_state(ticker: str) -> dict:
    return {
        "ticker": ticker.upper().strip(),
        "fundamental_report": {},
        "technical_report": {},
        "news_report": {},
        "sentiment_report": {},
        "analysts_merged": False,
        "bull_report": {},
        "bear_report": {},
        "research_merged": False,
        "trader_report": {},
        "risk_report": {},
        "fund_manager_report": {},
        "final_decision": "HOLD",
    }


def run_trading_workflow(ticker: str) -> dict:
    """Run the complete trading workflow for a given ticker."""
    if not ticker or not ticker.strip():
        state = _initial_state("")
        state["fundamental_report"] = _fundamental_fallback("", "Ticker cannot be empty")
        state["technical_report"] = _technical_fallback("", "Ticker cannot be empty")
        state["news_report"] = _news_fallback("", "Ticker cannot be empty")
        state["sentiment_report"] = _sentiment_fallback("", "Ticker cannot be empty")
        return state

    initial_state = _initial_state(ticker)

    try:
        graph = build_trading_graph()
        return graph.invoke(initial_state)
    except Exception as e:
        state = _initial_state(ticker)
        state["fund_manager_report"] = _fund_manager_fallback(ticker, str(e))
        state["final_decision"] = "HOLD"
        return state


if __name__ == "__main__":
    result = run_trading_workflow("AAPL")
    print(result)
