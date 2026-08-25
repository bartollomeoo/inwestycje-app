# Aplikacja wspomagająca inwestycje giełdowe na bazie PostgreSQL

Wersja przygotowana pod pracę grupową i wdrożenie online.

## Architektura

- Streamlit = interfejs i uruchomienie aplikacji
- PostgreSQL = trwała baza danych
- Supabase = opcjonalny dostawca PostgreSQL (connection string z panelu Supabase)
- yfinance = dane rynkowe
- Plotly = wykresy


## Podział pracy w grupie

- `db.py`, `transactions.py`, `migrate_sqlite_to_postgres.py` — baza/backend
- `auth.py`, `ui_login.py`, `ui_sidebar.py` — logowanie i konta
- `market.py`, `portfolio.py` — dane giełdowe i logika finansowa
- `charts.py`, `reports.py`, `ui_tabs.py` — wizualizacja i UI
- `app.py` — integracja całości


## Uruchamianie i ponowne renderowanie

Plik `run.py` wywołuje funkcję `main()` z pakietu aplikacji. Dzięki temu
`st.rerun()` działa poprawnie po logowaniu, wylogowaniu, zmianach transakcji
i imporcie CSV. 
