import numpy as np
import pandas as pd
from .market import get_latest_market_price


def calculate_portfolio(transactions: pd.DataFrame) -> pd.DataFrame:
    if transactions.empty:
        return pd.DataFrame()

    rows = []
    for ticker, group in transactions.groupby("ticker"):
        buys = group[group["transaction_type"] == "buy"].copy()
        sells = group[group["transaction_type"] == "sell"].copy()

        bought_qty = buys["quantity"].sum()
        sold_qty = sells["quantity"].sum()
        current_qty = bought_qty - sold_qty

        gross_buy_value = (buys["quantity"] * buys["price"]).sum()
        buy_fees = buys["fee"].sum()
        gross_sell_value = (sells["quantity"] * sells["price"]).sum()
        sell_fees = sells["fee"].sum()

        avg_buy_price = ((gross_buy_value + buy_fees) / bought_qty) if bought_qty > 0 else 0
        realized_pl = gross_sell_value - sell_fees - (avg_buy_price * sold_qty)

        latest_price, latest_date, source = get_latest_market_price(ticker)
        if latest_price is not None:
            market_price = latest_price
            market_value = current_qty * market_price
            unrealized_pl = market_value - (current_qty * avg_buy_price)
            total_pl = realized_pl + unrealized_pl
            profit_percent = (total_pl / (gross_buy_value + buy_fees) * 100) if gross_buy_value > 0 else 0
        else:
            market_price = np.nan
            market_value = np.nan
            unrealized_pl = np.nan
            total_pl = realized_pl
            profit_percent = np.nan
            latest_date = None

        rows.append({
            "Ticker": ticker,
            "Kupiono [szt.]": bought_qty,
            "Sprzedano [szt.]": sold_qty,
            "Aktualnie [szt.]": current_qty,
            "Średnia cena zakupu": avg_buy_price,
            "Koszt zakupu": gross_buy_value + buy_fees,
            "Przychód ze sprzedaży": gross_sell_value - sell_fees,
            "Zrealizowany P/L": realized_pl,
            "Aktualny kurs": market_price,
            "Data kursu": latest_date,
            "Wartość rynkowa": market_value,
            "Niezrealizowany P/L": unrealized_pl,
            "Łączny P/L": total_pl,
            "Stopa zwrotu [%]": profit_percent,
        })

    return pd.DataFrame(rows).sort_values("Łączny P/L", ascending=False)
