import os

import streamlit as st
import psycopg
from psycopg.rows import dict_row


def get_database_url() -> str:
    """Pobiera connection string PostgreSQL z secrets albo zmiennej środowiskowej."""
    try:
        value = st.secrets.get("DATABASE_URL")
    except Exception:
        value = None

    value = value or os.getenv("DATABASE_URL")
    if not value:
        raise RuntimeError(
            "Brak DATABASE_URL. Utwórz .streamlit/secrets.toml lokalnie albo "
            "dodaj DATABASE_URL w Secrets na Streamlit Community Cloud."
        )
    return str(value)


def get_connection():
    return psycopg.connect(get_database_url(), row_factory=dict_row)


def init_db():
    """Tworzy schemat PostgreSQL, jeśli jeszcze go nie ma."""
    connection = get_connection()
    try:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id BIGSERIAL PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                trade_date DATE NOT NULL,
                ticker TEXT NOT NULL,
                transaction_type TEXT NOT NULL,
                quantity DOUBLE PRECISION NOT NULL,
                price DOUBLE PRECISION NOT NULL,
                fee DOUBLE PRECISION NOT NULL DEFAULT 0
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                created_at TIMESTAMPTZ NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL
            )
        """)
        connection.execute("CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_transactions_ticker ON transactions(ticker)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_reports_user_id ON reports(user_id)")
        connection.commit()
    finally:
        connection.close()


def query_all(sql: str, params=()):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()
    finally:
        connection.close()
