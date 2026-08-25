from datetime import date, datetime
import pandas as pd
import streamlit as st

from .charts import allocation_chart, comparison_chart, price_chart, profit_chart
from .market import get_latest_market_price, load_price_history
from .reports import build_report_text, read_reports, save_report
from .transactions import delete_transaction, import_csv_transactions, insert_transaction

PERIODS = ["1mo", "3mo", "6mo", "1y", "2y", "5y"]


def render_portfolio_tab(transactions, portfolio):
    st.subheader("Podsumowanie portfela")
    if transactions.empty:
        st.info("Brak danych do wyświetlenia. Dodaj pierwszą transakcję.")
        return
    cols = ["Ticker", "Kupiono [szt.]", "Sprzedano [szt.]", "Aktualnie [szt.]", "Średnia cena zakupu", "Aktualny kurs", "Data kursu", "Wartość rynkowa", "Łączny P/L", "Stopa zwrotu [%]"]
    st.dataframe(portfolio[cols], width="stretch")
    st.subheader("Ranking opłacalności")
    st.dataframe(portfolio[["Ticker", "Łączny P/L", "Stopa zwrotu [%]", "Wartość rynkowa"]], width="stretch")


def render_add_transaction_tab(user_id):
    st.subheader("Dodaj transakcję")
    st.markdown("Wpisz ticker spółki, a aplikacja spróbuje automatycznie pobrać ostatni dostępny kurs. Cenę możesz zostawić automatycznie pobraną albo poprawić ręcznie.")
    st.session_state.setdefault("transaction_ticker", "AAPL")
    st.session_state.setdefault("transaction_price", 100.0)
    st.session_state.setdefault("last_price_ticker", "")

    ticker_input = st.text_input("Ticker", key="transaction_ticker", help="Przykłady: AAPL, MSFT, NVDA, TSLA, PKO.WA")
    current_ticker = ticker_input.upper().strip()
    if current_ticker and current_ticker != st.session_state["last_price_ticker"]:
        latest_price, latest_date, source = get_latest_market_price(current_ticker)
        st.session_state["last_price_ticker"] = current_ticker
        if latest_price is not None:
            st.session_state["transaction_price"] = round(latest_price, 2)
            date_text = latest_date.strftime("%Y-%m-%d") if latest_date is not None and hasattr(latest_date, "strftime") else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.success(f"Pobrano kurs dla {current_ticker}: {latest_price:,.2f} — źródło: {source}, data: {date_text}")
        else:
            st.warning("Nie udało się pobrać kursu dla tego tickera. Sprawdź symbol albo wpisz cenę ręcznie.")

    if st.button("Odśwież cenę z yfinance"):
        latest_price, latest_date, source = get_latest_market_price(current_ticker)
        if latest_price is not None:
            st.session_state["transaction_price"] = round(latest_price, 2)
            date_text = latest_date.strftime("%Y-%m-%d") if latest_date is not None and hasattr(latest_date, "strftime") else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.success(f"Zaktualizowano cenę: {latest_price:,.2f} — źródło: {source}, data: {date_text}")
        else:
            st.error("Nie udało się pobrać ceny dla podanego tickera.")

    with st.form("transaction_form", clear_on_submit=False):
        trade_date = st.date_input("Data transakcji", value=date.today())
        transaction_type = st.selectbox("Typ transakcji", ["buy", "sell"], format_func=lambda x: "Kupno" if x == "buy" else "Sprzedaż")
        quantity = st.number_input("Liczba akcji", min_value=0.0, value=1.0, step=1.0)
        price = st.number_input("Cena za akcję", min_value=0.0, step=0.10, key="transaction_price")
        fee = st.number_input("Prowizja", min_value=0.0, value=0.0, step=0.01)
        submitted = st.form_submit_button("Zapisz transakcję")
        if submitted:
            try:
                insert_transaction(user_id, trade_date, current_ticker, transaction_type, quantity, price, fee)
                st.success("Transakcja została dodana.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))


def render_sell_tab(user_id, transactions, portfolio):
    st.subheader("Sprzedaż akcji")
    if transactions.empty:
        st.info("Najpierw dodaj przynajmniej jedną transakcję kupna.")
        return
    active = portfolio[portfolio["Aktualnie [szt.]" ] > 0].copy()
    if active.empty:
        st.info("Nie masz aktualnie żadnych aktywnych pozycji do sprzedaży.")
        return
    selected_ticker = st.selectbox("Wybierz spółkę do sprzedaży", active["Ticker"].tolist(), key="sell_selected_ticker")
    row = active[active["Ticker"] == selected_ticker].iloc[0]
    current_quantity = float(row["Aktualnie [szt.]"])
    avg_buy_price = float(row["Średnia cena zakupu"])
    latest_price, latest_date, source = get_latest_market_price(selected_ticker)
    if latest_price is not None:
        current_price = float(latest_price)
        date_text = latest_date.strftime("%Y-%m-%d") if latest_date is not None and hasattr(latest_date, "strftime") else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.success(f"Pobrano aktualny kurs dla {selected_ticker}: {current_price:,.2f} | źródło: {source} | data: {date_text}")
    else:
        current_price = float(row["Aktualny kurs"]) if pd.notna(row["Aktualny kurs"]) else 100.0
        st.warning("Nie udało się pobrać aktualnego kursu z yfinance. Możesz wpisać cenę sprzedaży ręcznie.")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ticker", selected_ticker)
    c2.metric("Posiadane akcje", f"{current_quantity:,.0f}")
    c3.metric("Średnia cena zakupu", f"{avg_buy_price:,.2f}")
    c4.metric("Aktualny kurs", f"{current_price:,.2f}")
    st.divider()
    sell_date = st.date_input("Data sprzedaży", value=date.today(), key="sell_date")
    sell_price = st.number_input("Cena sprzedaży", min_value=0.0, value=round(current_price, 2), step=0.01, key=f"sell_price_{selected_ticker}")
    quantity_to_sell = st.number_input("Liczba akcji do sprzedaży", min_value=0.0, max_value=current_quantity, value=current_quantity, step=1.0, key=f"sell_quantity_{selected_ticker}")
    sell_fee = st.number_input("Prowizja sprzedaży", min_value=0.0, value=0.0, step=0.01, key=f"sell_fee_{selected_ticker}")
    estimated_pl = ((sell_price - avg_buy_price) * quantity_to_sell) - sell_fee
    st.metric("Szacowany zysk/strata ze sprzedaży", f"{estimated_pl:,.2f}")
    if st.button("Sprzedaj", key="sell_button"):
        try:
            if quantity_to_sell <= 0:
                st.error("Liczba akcji do sprzedaży musi być większa od zera.")
            elif quantity_to_sell > current_quantity:
                st.error("Nie możesz sprzedać więcej akcji niż posiadasz.")
            else:
                insert_transaction(user_id, sell_date, selected_ticker, "sell", quantity_to_sell, sell_price, sell_fee)
                st.success(f"Sprzedaż została zapisana: {selected_ticker}, {quantity_to_sell:,.0f} szt. po {sell_price:,.2f}")
                st.rerun()
        except Exception as exc:
            st.error(str(exc))


def render_analysis_tab(transactions):
    st.subheader("Szczegółowa analiza spółki")
    if transactions.empty:
        st.info("Najpierw dodaj przynajmniej jedną transakcję.")
        return
    tickers = sorted(transactions["ticker"].unique().tolist())
    ticker = st.selectbox("Spółka", tickers, key="analysis_ticker")
    period = st.selectbox("Zakres danych", PERIODS, index=3)
    history = load_price_history(ticker, period=period)
    if history.empty:
        st.warning("Brak danych dla wybranego tickera. Sprawdź symbol spółki.")
        return
    st.plotly_chart(price_chart(history, ticker), width="stretch")
    close = history["Close"]
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Średnia cena", f"{close.mean():,.2f}")
    s2.metric("Minimum", f"{close.min():,.2f}")
    s3.metric("Maksimum", f"{close.max():,.2f}")
    s4.metric("Odchylenie standardowe", f"{close.std():,.2f}")
    change = close.iloc[-1] - close.iloc[0]
    st.metric("Zmiana w analizowanym okresie", f"{change:,.2f}", f"{change / close.iloc[0] * 100:,.2f}%")


def render_comparison_tab(transactions):
    st.subheader("Porównanie historyczne spółek")
    if transactions.empty:
        st.info("Najpierw dodaj przynajmniej jedną transakcję.")
        return
    choices = sorted(transactions["ticker"].unique().tolist())
    selected = st.multiselect("Wybierz tickery", choices, default=choices[:3])
    period = st.selectbox("Zakres porównania", PERIODS, index=3, key="compare_period")
    if selected:
        st.plotly_chart(comparison_chart(selected, period), width="stretch")
    else:
        st.info("Wybierz co najmniej jeden ticker.")


def render_charts_tab(transactions, portfolio):
    st.subheader("Wykresy portfela")
    if transactions.empty:
        st.info("Brak danych do wygenerowania wykresów.")
        return
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(profit_chart(portfolio), width="stretch")
    with col2:
        fig = allocation_chart(portfolio)
        if fig:
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("Brak aktywnych pozycji do pokazania struktury portfela.")


def render_history_tab(user_id, transactions):
    st.subheader("Historia transakcji")
    if transactions.empty:
        st.info("Brak zapisanych transakcji.")
        return
    show_df = transactions.copy()
    show_df.insert(0, "Lp.", range(1, len(show_df) + 1))
    show_df["transaction_type"] = show_df["transaction_type"].replace({"buy": "kupno", "sell": "sprzedaż"})
    st.dataframe(show_df[["Lp.", "trade_date", "ticker", "transaction_type", "quantity", "price", "fee"]], width="stretch")
    st.subheader("Usuwanie transakcji")
    options = show_df[["Lp.", "id", "ticker", "trade_date"]].copy()
    options["opis"] = options.apply(lambda r: f'{r["Lp."]}. {r["ticker"]} — {r["trade_date"].strftime("%Y-%m-%d")} — ID {r["id"]}', axis=1)
    selected_description = st.selectbox("Wybierz transakcję do usunięcia", options["opis"].tolist())
    selected_id = int(options[options["opis"] == selected_description]["id"].iloc[0])
    if st.button("Usuń wybraną transakcję"):
        delete_transaction(user_id, selected_id)
        st.success("Transakcja została usunięta.")
        st.rerun()


def render_reports_tab(user_id, username, transactions, portfolio):
    st.subheader("Raporty")
    if transactions.empty:
        st.info("Brak danych do wygenerowania raportu.")
    else:
        report_content = build_report_text(username, portfolio, transactions)
        st.text_area("Podgląd raportu", report_content, height=420)
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Zapisz raport do historii"):
                title = f"Raport portfela - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                save_report(user_id, title, report_content)
                st.success("Raport został zapisany.")
                st.rerun()
        with col_b:
            st.download_button("Pobierz raport TXT", report_content, file_name="raport_portfela.txt", mime="text/plain")
    st.divider()
    st.subheader("Historia zapisanych raportów")
    reports = read_reports(user_id)
    if reports.empty:
        st.info("Nie zapisano jeszcze żadnego raportu.")
    else:
        for _, row in reports.iterrows():
            with st.expander(f'{row["created_at"]} — {row["title"]}'):
                st.text(row["content"])


def render_import_export_tab(user_id, transactions, portfolio):
    st.subheader("Import danych z CSV")
    st.markdown("Możesz wgrać plik CSV z transakcjami, np. przygotowany ręcznie albo na podstawie danych zewnętrznych.")
    uploaded_csv = st.file_uploader("Wgraj plik CSV z transakcjami", type=["csv"], key="csv_import_export_tab")
    if uploaded_csv is not None and st.button("Importuj transakcje z CSV"):
        try:
            csv_df = pd.read_csv(uploaded_csv)
            count = import_csv_transactions(user_id, csv_df)
            st.success(f"Zaimportowano transakcje: {count}")
            st.rerun()
        except Exception as exc:
            st.error(f"Import CSV nie powiódł się: {exc}")
    with st.expander("Wymagany format CSV"):
        st.code("trade_date,ticker,transaction_type,quantity,price,fee\n2026-03-01,AAPL,buy,10,210.50,2.99\n2026-03-15,AAPL,sell,3,219.80,2.99", language="csv")
    st.divider()
    st.subheader("Eksport danych")
    if transactions.empty:
        st.info("Brak danych do eksportu.")
    else:
        st.download_button("Pobierz transakcje CSV", transactions.to_csv(index=False).encode("utf-8"), file_name="transactions_export.csv", mime="text/csv")
        st.download_button("Pobierz podsumowanie portfela CSV", portfolio.to_csv(index=False).encode("utf-8"), file_name="portfolio_summary.csv", mime="text/csv")
    st.divider()
    st.subheader("Informacje o projekcie")
    st.markdown("""
    **Wersja chmurowa:**
    - baza danych PostgreSQL,
    - sekrety trzymane poza repozytorium,
    - gotowość do wdrożenia na Streamlit Community Cloud.
    """)
