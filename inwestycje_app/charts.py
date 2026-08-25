import plotly.graph_objects as go
from .market import load_price_history


def price_chart(history_df, ticker: str):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=history_df["Date"], y=history_df["Close"], mode="lines", name="Cena"
    ))
    fig.update_layout(
        title=f"Notowania {ticker}", xaxis_title="Data", yaxis_title="Cena",
        height=450, margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig


def comparison_chart(tickers: list[str], period: str):
    fig = go.Figure()
    for ticker in tickers:
        history = load_price_history(ticker, period=period)
        if history.empty or "Close" not in history.columns:
            continue
        normalized = history["Close"] / history["Close"].iloc[0] * 100
        fig.add_trace(go.Scatter(
            x=history["Date"], y=normalized, mode="lines", name=ticker
        ))
    fig.update_layout(
        title="Porównanie historyczne spółek: start = 100",
        xaxis_title="Data", yaxis_title="Indeks bazowy 100",
        height=500, margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig


def allocation_chart(portfolio):
    active = portfolio[portfolio["Aktualnie [szt.]" ] > 0].copy()
    if active.empty:
        return None
    fig = go.Figure(data=[go.Pie(
        labels=active["Ticker"], values=active["Wartość rynkowa"].fillna(0), hole=0.45
    )])
    fig.update_layout(
        title="Struktura portfela według wartości rynkowej",
        height=430, margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig


def profit_chart(portfolio):
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=portfolio["Ticker"], y=portfolio["Łączny P/L"], name="Łączny P/L"
    ))
    fig.update_layout(
        title="Zysk / strata według spółek",
        xaxis_title="Ticker", yaxis_title="Zysk / strata",
        height=430, margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig
