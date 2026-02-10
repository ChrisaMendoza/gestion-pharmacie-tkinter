from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_NAME = str(BASE_DIR / "database" / "pharmacie.db")

APP_NAME = "Système de Gestion de Pharmacie"
SESSION_TIMEOUT = 1800  # 30 minutes
