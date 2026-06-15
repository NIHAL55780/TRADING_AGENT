import json
import math
import os
import threading
from pathlib import Path

import requests
from dotenv import load_dotenv
from websocket import WebSocketApp

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

FINNHUB_QUOTE_URL = "https://finnhub.io/api/v1/quote"
FINNHUB_WS_URL = "wss://ws.finnhub.io"


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


def _get_api_key() -> str | None:
    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key or not api_key.strip():
        return None
    return api_key.strip()


def _normalize_ticker(ticker: str) -> str | None:
    if not ticker or not ticker.strip():
        return None
    return ticker.strip().upper()


def get_finnhub_quote(ticker: str) -> dict:
    symbol = _normalize_ticker(ticker)
    if not symbol:
        return {"error": "Ticker cannot be empty"}

    api_key = _get_api_key()
    if not api_key:
        return {"error": "FINNHUB_API_KEY environment variable is not set"}

    try:
        response = requests.get(
            FINNHUB_QUOTE_URL,
            params={"symbol": symbol, "token": api_key},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        if not isinstance(data, dict):
            return {"error": f"Unexpected response for ticker '{symbol}'"}

        if data.get("error"):
            return {"error": str(data["error"])}

        current_price = _safe_float(data.get("c"))
        previous_close = _safe_float(data.get("pc"))

        if current_price is None and previous_close is None:
            return {"error": f"No quote data found for ticker '{symbol}'"}

        return {
            "ticker": symbol,
            "current_price": current_price,
            "change": _safe_float(data.get("d")),
            "percent_change": _safe_float(data.get("dp")),
            "high": _safe_float(data.get("h")),
            "low": _safe_float(data.get("l")),
            "open": _safe_float(data.get("o")),
            "previous_close": previous_close,
            "timestamp": int(data["t"]) if data.get("t") is not None else None,
            "source": "Finnhub",
        }
    except requests.RequestException as e:
        return {"error": f"Finnhub quote request failed: {e}"}
    except Exception as e:
        return {"error": str(e)}


def get_live_trade_snapshot(ticker: str, timeout_seconds: int = 10) -> dict:
    symbol = _normalize_ticker(ticker)
    if not symbol:
        return {
            "ticker": "",
            "error": "Ticker cannot be empty",
            "source": "Finnhub WebSocket",
        }

    api_key = _get_api_key()
    if not api_key:
        return {
            "ticker": symbol,
            "error": "FINNHUB_API_KEY environment variable is not set",
            "source": "Finnhub WebSocket",
        }

    if timeout_seconds <= 0:
        return {
            "ticker": symbol,
            "error": "timeout_seconds must be greater than 0",
            "source": "Finnhub WebSocket",
        }

    latest_trade: dict | None = None
    ws_error: str | None = None
    done = threading.Event()
    ws_app: WebSocketApp | None = None

    def on_open(ws: WebSocketApp) -> None:
        ws.send(json.dumps({"type": "subscribe", "symbol": symbol}))

    def on_message(_ws: WebSocketApp, message: str) -> None:
        nonlocal latest_trade
        try:
            payload = json.loads(message)
        except json.JSONDecodeError:
            return

        if payload.get("type") != "trade":
            return

        for trade in payload.get("data", []):
            if trade.get("s") != symbol:
                continue

            price = _safe_float(trade.get("p"))
            if price is None:
                continue

            latest_trade = {
                "ticker": symbol,
                "price": price,
                "volume": _safe_float(trade.get("v")) or 0.0,
                "timestamp": int(trade["t"]) if trade.get("t") is not None else None,
                "source": "Finnhub WebSocket",
            }
            done.set()
            if ws_app is not None:
                ws_app.close()
            return

    def on_error(_ws: WebSocketApp, error) -> None:
        nonlocal ws_error
        ws_error = str(error)
        done.set()

    def on_close(_ws: WebSocketApp, _close_status_code, _close_msg) -> None:
        done.set()

    try:
        ws_app = WebSocketApp(
            f"{FINNHUB_WS_URL}?token={api_key}",
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
        )

        ws_thread = threading.Thread(
            target=ws_app.run_forever,
            kwargs={"ping_interval": 20, "ping_timeout": 10},
            daemon=True,
        )
        ws_thread.start()

        if not done.wait(timeout=timeout_seconds):
            ws_app.close()
            ws_thread.join(timeout=2)
            return {
                "ticker": symbol,
                "error": f"No trade received within {timeout_seconds} seconds",
                "source": "Finnhub WebSocket",
            }

        if latest_trade is not None:
            return latest_trade

        return {
            "ticker": symbol,
            "error": ws_error or "WebSocket connection closed without receiving a trade",
            "source": "Finnhub WebSocket",
        }
    except Exception as e:
        return {
            "ticker": symbol,
            "error": str(e),
            "source": "Finnhub WebSocket",
        }
    finally:
        if ws_app is not None:
            try:
                ws_app.close()
            except Exception:
                pass


if __name__ == "__main__":
    print("Finnhub quote:")
    print(get_finnhub_quote("AAPL"))

    print("\nFinnhub live trade snapshot:")
    print(get_live_trade_snapshot("AAPL", timeout_seconds=10))

