import yfinance as yf


def get_market_data(ticker: str) -> dict:
    if not ticker or not ticker.strip():
        return {"error": "Ticker cannot be empty"}

    ticker = ticker.strip().upper()

    try:
        info = yf.Ticker(ticker).info

        if not info or info.get("regularMarketPrice") is None and info.get("currentPrice") is None:
            return {"error": f"No market data found for ticker '{ticker}'"}

        current_price = info.get("currentPrice") or info.get("regularMarketPrice")
        previous_close = info.get("previousClose") or info.get("regularMarketPreviousClose")
        open_price = info.get("open") or info.get("regularMarketOpen")
        day_high = info.get("dayHigh") or info.get("regularMarketDayHigh")
        day_low = info.get("dayLow") or info.get("regularMarketDayLow")
        volume = info.get("volume") or info.get("regularMarketVolume")
        market_cap = info.get("marketCap")

        return {
            "ticker": ticker,
            "current_price": float(current_price) if current_price is not None else None,
            "previous_close": float(previous_close) if previous_close is not None else None,
            "open": float(open_price) if open_price is not None else None,
            "day_high": float(day_high) if day_high is not None else None,
            "day_low": float(day_low) if day_low is not None else None,
            "volume": int(volume) if volume is not None else None,
            "market_cap": float(market_cap) if market_cap is not None else None,
        }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    print(get_market_data("AAPL"))
