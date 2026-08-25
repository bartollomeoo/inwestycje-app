from datetime import datetime, timezone
import numpy as np
import pandas as pd
from .db import get_connection


def build_report_text(username: str, portfolio: pd.DataFrame, transactions: pd.DataFrame) -> str:
    if portfolio.empty:
        return "Brak danych do wygenerowania raportu."

    total_cost = portfolio["Koszt zakupu"].sum()
    total_market_value = np.nansum(portfolio["Wartość rynkowa"])
    total_realized = portfolio["Zrealizowany P/L"].sum()
    total_unrealized = np.nansum(portfolio["Niezrealizowany P/L"])
    total_pl = np.nansum(portfolio["Łączny P/L"])
    best_row = portfolio.iloc[0]
    worst_row = portfolio.iloc[-1]

    return f"""RAPORT ANALIZY PORTFELA INWESTYCYJNEGO

Użytkownik: {username}
Data wygenerowania raportu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Źródło danych rynkowych: yfinance / Yahoo Finance

1. PODSUMOWANIE OGÓLNE

Łączny koszt zakupu: {total_cost:,.2f}
Aktualna wartość rynkowa: {total_market_value:,.2f}
Zrealizowany zysk/strata: {total_realized:,.2f}
Niezrealizowany zysk/strata: {total_unrealized:,.2f}
Łączny wynik portfela: {total_pl:,.2f}

2. NAJBARDZIEJ OPŁACALNA SPÓŁKA

Ticker: {best_row['Ticker']}
Łączny P/L: {best_row['Łączny P/L']:,.2f}
Stopa zwrotu: {best_row['Stopa zwrotu [%]']:,.2f}%

3. NAJSŁABSZA SPÓŁKA W PORTFELU

Ticker: {worst_row['Ticker']}
Łączny P/L: {worst_row['Łączny P/L']:,.2f}
Stopa zwrotu: {worst_row['Stopa zwrotu [%]']:,.2f}%

4. LICZBA TRANSAKCJI

Liczba wszystkich transakcji: {len(transactions)}
Liczba instrumentów w portfelu: {portfolio['Ticker'].nunique()}
""".strip()


def save_report(user_id: int, title: str, content: str):
    connection = get_connection()
    try:
        connection.execute(
            "INSERT INTO reports (user_id, created_at, title, content) VALUES (%s, %s, %s, %s)",
            (int(user_id), datetime.now(timezone.utc), title, content)
        )
        connection.commit()
    finally:
        connection.close()


def read_reports(user_id: int) -> pd.DataFrame:
    connection = get_connection()
    try:
        rows = connection.execute(
            "SELECT id, created_at, title, content FROM reports WHERE user_id = %s ORDER BY created_at DESC",
            (int(user_id),)
        ).fetchall()
    finally:
        connection.close()
    if not rows:
        return pd.DataFrame(columns=["id", "created_at", "title", "content"])
    return pd.DataFrame(rows)
