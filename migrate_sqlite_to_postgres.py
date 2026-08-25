"""Jednorazowa migracja starej lokalnej baza.db do PostgreSQL.

Użycie:
    DATABASE_URL="..." python migrate_sqlite_to_postgres.py
"""
from pathlib import Path
import os
import sqlite3
import psycopg

SQLITE_PATH = Path(os.getenv("LEGACY_DB_PATH", "baza.db"))
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise SystemExit("Brak DATABASE_URL w zmiennych środowiskowych.")
if not SQLITE_PATH.exists():
    raise SystemExit(f"Nie znaleziono pliku SQLite: {SQLITE_PATH}")


def init_schema(connection):
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


def main():
    sqlite = sqlite3.connect(SQLITE_PATH)
    sqlite.row_factory = sqlite3.Row

    with psycopg.connect(DATABASE_URL) as pg:
        init_schema(pg)

        users = sqlite.execute("SELECT id, username, password_hash, created_at FROM users ORDER BY id").fetchall()
        transactions = sqlite.execute("SELECT id, user_id, trade_date, ticker, transaction_type, quantity, price, fee FROM transactions ORDER BY id").fetchall()
        reports = sqlite.execute("SELECT id, user_id, created_at, title, content FROM reports ORDER BY id").fetchall()

        for row in users:
            pg.execute(
                """INSERT INTO users (id, username, password_hash, created_at)
                   VALUES (%s, %s, %s, %s)
                   ON CONFLICT (id) DO UPDATE SET
                     username = EXCLUDED.username,
                     password_hash = EXCLUDED.password_hash,
                     created_at = EXCLUDED.created_at""",
                tuple(row),
            )

        for row in transactions:
            pg.execute(
                """INSERT INTO transactions
                   (id, user_id, trade_date, ticker, transaction_type, quantity, price, fee)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                   ON CONFLICT (id) DO NOTHING""",
                tuple(row),
            )

        for row in reports:
            pg.execute(
                """INSERT INTO reports (id, user_id, created_at, title, content)
                   VALUES (%s, %s, %s, %s, %s)
                   ON CONFLICT (id) DO NOTHING""",
                tuple(row),
            )

        pg.execute("SELECT setval(pg_get_serial_sequence('users','id'), COALESCE(MAX(id), 1), MAX(id) IS NOT NULL) FROM users")
        pg.execute("SELECT setval(pg_get_serial_sequence('transactions','id'), COALESCE(MAX(id), 1), MAX(id) IS NOT NULL) FROM transactions")
        pg.execute("SELECT setval(pg_get_serial_sequence('reports','id'), COALESCE(MAX(id), 1), MAX(id) IS NOT NULL) FROM reports")
        pg.commit()

    sqlite.close()
    print(f"Migracja zakończona. users={len(users)}, transactions={len(transactions)}, reports={len(reports)}")


if __name__ == "__main__":
    main()
