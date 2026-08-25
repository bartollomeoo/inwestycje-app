import numpy as np
import streamlit as st

from .config import APP_TITLE
from .db import init_db
from .portfolio import calculate_portfolio
from .transactions import read_transactions
from .ui_login import show_login_screen
from .ui_sidebar import render_sidebar
from .ui_tabs import (
    render_add_transaction_tab,
    render_analysis_tab,
    render_charts_tab,
    render_comparison_tab,
    render_history_tab,
    render_import_export_tab,
    render_portfolio_tab,
    render_reports_tab,
    render_sell_tab,
)


def main():
    """Główny przebieg aplikacji Streamlit.

    Funkcja jest wywoływana z run.py przy każdym wykonaniu skryptu przez
    Streamlit. Dzięki temu st.rerun() poprawnie odtwarza cały interfejs,
    zamiast polegać na ponownym imporcie już zbuforowanego modułu.
    """
    st.set_page_config(page_title=APP_TITLE, layout="wide")

    try:
        init_db()
    except Exception as exc:
        st.error(f"Nie udało się połączyć z bazą PostgreSQL: {exc}")
        st.stop()

    if "user_id" not in st.session_state:
        show_login_screen()
        st.stop()

    user_id = st.session_state["user_id"]
    username = st.session_state["username"]

    st.title(APP_TITLE)
    render_sidebar(user_id, username)

    try:
        transactions = read_transactions(user_id)
        portfolio = calculate_portfolio(transactions)
    except Exception as exc:
        st.error(f"Nie udało się wczytać danych użytkownika: {exc}")
        st.stop()

    if transactions.empty:
        st.info(
            "Nie masz jeszcze żadnych transakcji. "
            "Przejdź do zakładki „Dodaj transakcję”."
        )
    else:
        total_cost = portfolio["Koszt zakupu"].sum() if not portfolio.empty else 0
        total_market_value = (
            np.nansum(portfolio["Wartość rynkowa"])
            if not portfolio.empty
            else 0
        )
        total_pl = (
            np.nansum(portfolio["Łączny P/L"])
            if not portfolio.empty
            else 0
        )
        best_ticker = portfolio.iloc[0]["Ticker"] if not portfolio.empty else "-"

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Łączny koszt zakupu", f"{total_cost:,.2f}")
        c2.metric("Aktualna wartość", f"{total_market_value:,.2f}")
        c3.metric("Łączny P/L", f"{total_pl:,.2f}")
        c4.metric("Najbardziej opłacalna spółka", best_ticker)

    tabs = st.tabs(
        [
            "Portfel",
            "Dodaj transakcję",
            "Sprzedaż",
            "Analiza spółki",
            "Porównanie spółek",
            "Wykresy",
            "Historia transakcji",
            "Raporty",
            "Eksport, import i informacje",
        ]
    )

    with tabs[0]:
        render_portfolio_tab(transactions, portfolio)
    with tabs[1]:
        render_add_transaction_tab(user_id)
    with tabs[2]:
        render_sell_tab(user_id, transactions, portfolio)
    with tabs[3]:
        render_analysis_tab(transactions)
    with tabs[4]:
        render_comparison_tab(transactions)
    with tabs[5]:
        render_charts_tab(transactions, portfolio)
    with tabs[6]:
        render_history_tab(user_id, transactions)
    with tabs[7]:
        render_reports_tab(user_id, username, transactions, portfolio)
    with tabs[8]:
        render_import_export_tab(user_id, transactions, portfolio)
