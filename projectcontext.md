# Multi-Agent Trading System

## Project Overview
Building an intelligent **multi-agent trading system** that combines fundamental and technical analysis using LLMs (Groq) to provide stock recommendations.

## Architecture

### Core Components

**1. Multi-Agent System**
- **Fundamental Agent** (`agents/fundamental_agent.py`)
  - Analyzes company financials: growth, profitability, debt risk, financial strength
  - Returns: Stance (Bullish/Bearish/Neutral) + Confidence score (0-100) + Reasoning
  - Data Source: Financial metrics from `tools/financial_data.py`

- **Technical Agent** (`agents/technical_agent.py`)
  - Analyzes price trends, momentum, volatility, overbought/oversold conditions
  - Returns: Stance (Bullish/Bearish/Neutral) + Confidence score (0-100) + Reasoning
  - Data Source: Technical indicators from `tools/technical_indicators.py`

**2. Tools/Data Sources**
- `tools/financial_data.py` - Fetches company financial metrics (via yfinance)
- `tools/technical_indicators.py` - Calculates technical indicators (SMA, RSI, MACD, etc. using ta)
- `tools/llm.py` - LLM interface to Groq for analysis
- `tools/market_data.py` - Real-time market data
- `tools/sentiment_data.py` - Market sentiment analysis
- `tools/news_data.py` - Financial news aggregation

**3. Backend Services**
- `main.py` - FastAPI application (orchestrates agents)
- `config.py` - Configuration management
- MongoDB - Data persistence layer

## Tech Stack
- **Framework**: FastAPI + Uvicorn (API server)
- **LLM**: Groq + LangChain
- **Agent Orchestration**: LangGraph
- **Data**: yfinance, pandas, numpy
- **Technical Analysis**: ta (technical analysis indicators)
- **Database**: MongoDB
- **Configuration**: python-dotenv

## Agent Response Format
```json
{
  "agent": "Agent Name",
  "ticker": "STOCK_SYMBOL",
  "stance": "Bullish | Bearish | Neutral",
  "confidence": 0-100,
  "reason": "Brief explanation",
  "raw_data": {}
}
```

## Development Status
- ✅ Agent logic implemented (fundamental + technical)
- ✅ Error handling and fallbacks
- ✅ LangGraph workflow integration (Phase 5 - Sequential)
- ✅ Parallel execution with merge (Phase 6)
- ✅ Bull vs Bear debate agents (Phase 7)
- ✅ Trader agent (Phase 8)
- ✅ Risk Manager agent (Phase 9)
- ✅ Fund Manager agent (Phase 10)
- ⏳ Integrated workflow in LangGraph
- ⏳ FastAPI endpoints (main.py)

## Phase 5-10: Complete Agent System (✅ Complete)

### Agent Pipeline:
```
START
  ├── Fundamental Analysis (parallel)
  └── Technical Analysis (parallel)
        ↓
    Merge Node
        ↓
    Bull Researcher (BUY arguments)
        ↓
    Bear Researcher (AVOID arguments)
        ↓
    Trader Agent (BUY/SELL/HOLD decision)
        ↓
    Risk Manager (Risk assessment, position sizing)
        ↓
    Fund Manager (Final decision, execute=false always)
        ↓
      END
```

### Phase 8: Trader Agent (`backend/agents/trader_agent.py`) ✅
- **Function**: `run_trader_agent(ticker, fundamental_report, technical_report, bull_report, bear_report, news_report=None, sentiment_report=None)`
- **Decision**: BUY, SELL, or HOLD
- **Returns**: decision, confidence (0-100), reason, bull_case_strength, bear_case_strength
- **Logic**: Compares bullish and bearish evidence using LLM
- **Key Feature**: Research-only recommendation, no execution

### Phase 9: Risk Manager Agent (`backend/agents/risk_manager_agent.py`) ✅
- **Function**: `run_risk_manager_agent(ticker, trader_report, technical_report)`
- **Risk Levels**: Low, Medium, High
- **Position Sizes**: 0%, 1%, 3%, 5%
- **Logic**: Rule-based + optional LLM explanation
  - High Risk: volatility ≥ 0.40 OR RSI ≥ 75 OR RSI ≤ 25 OR confidence < 50
  - Medium Risk: volatility ≥ 0.25 OR RSI ≥ 70 OR RSI ≤ 30 OR confidence < 65
  - Low Risk: Otherwise
- **Position Sizing**: Based on risk level and trader decision
- **Approval**: false for HOLD/SELL, true for BUY (with reduced size if High risk)

### Phase 10: Fund Manager Agent (`backend/agents/fund_manager_agent.py`) ✅
- **Function**: `run_fund_manager_agent(ticker, trader_report, risk_report, fundamental_report=None, technical_report=None, bull_report=None, bear_report=None)`
- **Final Decision**: BUY, SELL, or HOLD
- **Returns**: final_decision, confidence, position_size, **execute=false** (always)
- **Logic**: LLM synthesizes all reports into final recommendation
- **Key Feature**: `execute` is ALWAYS false - research-only platform

## Next Steps
1. Integrate all agents into LangGraph workflow
2. Implement FastAPI endpoints in main.py
3. Create request/response models
4. Test full pipeline end-to-end
5. Deploy with uvicorn
