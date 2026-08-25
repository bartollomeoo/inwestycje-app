import os
from pathlib import Path

APP_TITLE = "Aplikacja wspomagająca inwestycje giełdowe"
PRICE_CACHE_TTL = 1800
LATEST_PRICE_CACHE_TTL = 300

# Lokalne SQLite pozostaje wyłącznie do jednorazowej migracji.
LEGACY_DB_PATH = Path(os.getenv("LEGACY_DB_PATH", "baza.db"))
