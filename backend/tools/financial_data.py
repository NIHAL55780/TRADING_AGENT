import math

import yfinance as yf


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


def _get_statement_value(df, *row_names: str) -> float | None:
    if df is None or df.empty:
        return None

    for name in row_names:
        if name not in df.index:
            continue
        value = df.loc[name].iloc[0]
        result = _safe_float(value)
        if result is not None:
            return result

    return None


def get_financial_data(ticker: str) -> dict:
    if not ticker or not ticker.strip():
        return {"error": "Ticker cannot be empty"}

    symbol = ticker.strip().upper()

    try:
        stock = yf.Ticker(symbol)
        info = stock.info or {}

        financials = stock.financials
        balance_sheet = stock.balance_sheet

        revenue = _get_statement_value(
            financials,
            "Total Revenue",
            "TotalRevenue",
            "Revenue",
        )
        gross_profit = _get_statement_value(financials, "Gross Profit", "GrossProfit")
        net_income = _get_statement_value(
            financials,
            "Net Income",
            "Net Income Common Stockholders",
            "NetIncome",
        )

        total_debt = _get_statement_value(
            balance_sheet,
            "Total Debt",
            "Long Term Debt And Capital Lease Obligation",
            "Long Term Debt",
        )
        total_cash = _get_statement_value(
            balance_sheet,
            "Cash And Cash Equivalents",
            "Cash Cash Equivalents And Short Term Investments",
            "Cash And Cash Equivalents And Short Term Investments",
        )

        if total_cash is None:
            total_cash = _safe_float(info.get("totalCash"))

        if total_debt is None:
            total_debt = _safe_float(info.get("totalDebt"))

        eps = _safe_float(info.get("trailingEps") or info.get("epsTrailingTwelveMonths"))
        pe_ratio = _safe_float(
            info.get("trailingPE") or info.get("forwardPE") or info.get("priceToTrailingEps")
        )
        roe = _safe_float(info.get("returnOnEquity"))
        profit_margin = _safe_float(info.get("profitMargins"))
        debt_to_equity = _safe_float(info.get("debtToEquity"))

        if revenue is None and eps is None and pe_ratio is None:
            return {"error": f"No financial data found for ticker '{symbol}'"}

        return {
            "ticker": symbol,
            "revenue": revenue,
            "gross_profit": gross_profit,
            "net_income": net_income,
            "total_debt": total_debt,
            "total_cash": total_cash,
            "eps": eps,
            "pe_ratio": pe_ratio,
            "roe": roe,
            "profit_margin": profit_margin,
            "debt_to_equity": debt_to_equity,
        }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    print(get_financial_data("AAPL"))
