import pandas as pd
from .db import get_connection


def normalize_transaction_type(value: str) -> str:
    value = str(value).lower().strip()
    if value in ["buy", "kupno", "zakup", "k"]:
        return "buy"
    if value in ["sell", "sprzedaż", "sprzedaz", "s"]:
        return "sell"
    raise ValueError("Typ transakcji musi być: buy/sell albo kupno/sprzedaż.")


def insert_transaction(user_id, trade_date, ticker, transaction_type, quantity, price, fee):
    ticker = str(ticker).upper().strip()
    transaction_type = normalize_transaction_type(transaction_type)
    if not ticker:
        raise ValueError("Ticker nie może być pusty.")
    if float(quantity) <= 0:
        raise ValueError("Liczba akcji musi być większa od zera.")
    if float(price) <= 0:
        raise ValueError("Cena musi być większa od zera.")
    if float(fee) < 0:
        raise ValueError("Prowizja nie może być ujemna.")

    connection = get_connection()
    try:
        connection.execute(
            """
            INSERT INTO transactions
            (user_id, trade_date, ticker, transaction_type, quantity, price, fee)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (int(user_id), trade_date, ticker, transaction_type,
             float(quantity), float(price), float(fee)),
        )
        connection.commit()
    finally:
        connection.close()


def read_transactions(user_id: int) -> pd.DataFrame:
    connection = get_connection()
    try:
        rows = connection.execute(
            """
            SELECT id, trade_date, ticker, transaction_type, quantity, price, fee
            FROM transactions
            WHERE user_id = %s
            ORDER BY trade_date, id
            """,
            (int(user_id),),
        ).fetchall()
    finally:
        connection.close()

    if not rows:
        return pd.DataFrame(columns=[
            "id", "trade_date", "ticker", "transaction_type", "quantity", "price", "fee"
        ])

    df = pd.DataFrame(rows)
    df["trade_date"] = pd.to_datetime(df["trade_date"])
    df["ticker"] = df["ticker"].astype(str).str.upper().str.strip()
    return df


def delete_transaction(user_id: int, row_id: int):
    connection = get_connection()
    try:
        connection.execute(
            "DELETE FROM transactions WHERE id = %s AND user_id = %s",
            (int(row_id), int(user_id)),
        )
        connection.commit()
    finally:
        connection.close()


def import_csv_transactions(user_id: int, df: pd.DataFrame):
    required = {"trade_date", "ticker", "transaction_type", "quantity", "price", "fee"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            "CSV musi zawierać kolumny: trade_date, ticker, transaction_type, "
            "quantity, price, fee. Brakuje: " + ", ".join(sorted(missing))
        )

    clean = df.copy()
    clean["trade_date"] = pd.to_datetime(clean["trade_date"], errors="raise").dt.date
    clean["ticker"] = clean["ticker"].astype(str).str.upper().str.strip()
    clean["transaction_type"] = clean["transaction_type"].apply(normalize_transaction_type)
    clean["quantity"] = pd.to_numeric(clean["quantity"], errors="raise")
    clean["price"] = pd.to_numeric(clean["price"], errors="raise")
    clean["fee"] = pd.to_numeric(clean["fee"], errors="raise").fillna(0)

    # Walidacja całego pliku przed pierwszym INSERT-em.
    if (clean["ticker"] == "").any():
        raise ValueError("CSV zawiera pusty ticker.")
    if (clean["quantity"] <= 0).any():
        raise ValueError("CSV zawiera ilość akcji <= 0.")
    if (clean["price"] <= 0).any():
        raise ValueError("CSV zawiera cenę <= 0.")
    if (clean["fee"] < 0).any():
        raise ValueError("CSV zawiera ujemną prowizję.")

    connection = get_connection()
    try:
        for _, row in clean.iterrows():
            connection.execute(
                """
                INSERT INTO transactions
                (user_id, trade_date, ticker, transaction_type, quantity, price, fee)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (int(user_id), row["trade_date"], row["ticker"], row["transaction_type"],
                 float(row["quantity"]), float(row["price"]), float(row["fee"])),
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    return len(clean)
