import math
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import numpy as np
import pandas as pd
import yfinance as yf
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACD, SMAIndicator
from ta.volatility import BollingerBands

from tools.finnhub_data import get_finnhub_quote

MIN_HISTORY_ROWS = 50


def _safe_float(value) -> float | None:
    if value is None:
        return None
    try:
        result = float(value)
        if math.isnan(result):
            return None
        return result
    except (TypeError, ValueError):
        return None


def _determine_trend(
    latest_close: float | None,
    sma_50: float | None,
    macd: float | None,
    macd_signal: float | None,
) -> str:
    if latest_close is None or sma_50 is None or macd is None or macd_signal is None:
        return "Neutral"
    if latest_close > sma_50 and macd > macd_signal:
        return "Bullish"
    if latest_close < sma_50 and macd < macd_signal:
        return "Bearish"
    return "Neutral"


def get_technical_indicators(ticker: str, period: str = "1y") -> dict:
    if not ticker or not ticker.strip():
        return {"error": "Ticker cannot be empty"}

    if not period or not period.strip():
        return {"error": "Period cannot be empty"}

    symbol = ticker.strip().upper()
    period = period.strip()

    try:
        history = yf.Ticker(symbol).history(period=period)

        if history is None or history.empty:
            return {"error": f"No historical data found for ticker '{symbol}'"}

        if "Close" not in history.columns:
            return {"error": f"Close price data unavailable for ticker '{symbol}'"}

        if len(history) < MIN_HISTORY_ROWS:
            return {
                "error": (
                    f"Insufficient historical data for ticker '{symbol}'. "
                    f"Need at least {MIN_HISTORY_ROWS} rows, got {len(history)}."
                )
            }

        close = history["Close"]

        sma_20_series = SMAIndicator(close=close, window=20).sma_indicator()
        sma_50_series = SMAIndicator(close=close, window=50).sma_indicator()
        ema_20_series = EMAIndicator(close=close, window=20).ema_indicator()
        rsi_14_series = RSIIndicator(close=close, window=14).rsi()

        macd_indicator = MACD(close=close)
        macd_series = macd_indicator.macd()
        macd_signal_series = macd_indicator.macd_signal()

        bollinger = BollingerBands(close=close, window=20)
        bollinger_upper_series = bollinger.bollinger_hband()
        bollinger_lower_series = bollinger.bollinger_lband()

        returns = close.pct_change().dropna()
        volatility = _safe_float(returns.std() * np.sqrt(252)) if not returns.empty else None

        latest_close = _safe_float(close.iloc[-1])
        sma_20 = _safe_float(sma_20_series.iloc[-1])
        sma_50 = _safe_float(sma_50_series.iloc[-1])
        ema_20 = _safe_float(ema_20_series.iloc[-1])
        rsi_14 = _safe_float(rsi_14_series.iloc[-1])
        macd = _safe_float(macd_series.iloc[-1])
        macd_signal = _safe_float(macd_signal_series.iloc[-1])
        bollinger_upper = _safe_float(bollinger_upper_series.iloc[-1])
        bollinger_lower = _safe_float(bollinger_lower_series.iloc[-1])

        if latest_close is None:
            return {"error": f"Unable to calculate indicators for ticker '{symbol}'"}

        live_price = latest_close
        price_source = "historical"

        finnhub_quote = get_finnhub_quote(symbol)
        if "error" not in finnhub_quote:
            finnhub_price = _safe_float(finnhub_quote.get("current_price"))
            if finnhub_price is not None:
                live_price = finnhub_price
                price_source = "Finnhub"

        trend = _determine_trend(latest_close, sma_50, macd, macd_signal)

        return {
            "ticker": symbol,
            "period": period,
            "latest_close": latest_close,
            "live_price": live_price,
            "price_source": price_source,
            "sma_20": sma_20,
            "sma_50": sma_50,
            "ema_20": ema_20,
            "rsi_14": rsi_14,
            "macd": macd,
            "macd_signal": macd_signal,
            "bollinger_upper": bollinger_upper,
            "bollinger_lower": bollinger_lower,
            "volatility": volatility,
            "trend": trend,
        }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    print(get_technical_indicators("AAPL"))
