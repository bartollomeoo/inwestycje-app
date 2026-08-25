from datetime import datetime

import pandas as pd
import streamlit as st
import yfinance as yf

from .config import LATEST_PRICE_CACHE_TTL, PRICE_CACHE_TTL


@st.cache_data(ttl=PRICE_CACHE_TTL)
def load_price_history(ticker: str, period: str = "1y") -> pd.DataFrame:
    try:
        ticker = ticker.upper().strip()
        data = yf.Ticker(ticker).history(period=period, auto_adjust=True)
        if data.empty:
            return pd.DataFrame()
        data = data.reset_index()
        if "Date" in data.columns:
            data["Date"] = pd.to_datetime(data["Date"]).dt.tz_localize(None)
        elif "Datetime" in data.columns:
            data["Date"] = pd.to_datetime(data["Datetime"]).dt.tz_localize(None)
        return data
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=LATEST_PRICE_CACHE_TTL)
def get_latest_market_price(ticker: str):
    ticker = ticker.upper().strip()
    if not ticker:
        return None, None, None

    try:
        fast_info = yf.Ticker(ticker).fast_info
        last_price = fast_info.get("last_price")
        if last_price is not None:
            return float(last_price), datetime.now(), "fast_info.last_price"
    except Exception:
        pass

    history = load_price_history(ticker, period="5d")
    if history.empty or "Close" not in history.columns:
        return None, None, None
    close_series = history["Close"].dropna()
    if close_series.empty:
        return None, None, None
    return float(close_series.iloc[-1]), history["Date"].iloc[-1], "history.Close"
