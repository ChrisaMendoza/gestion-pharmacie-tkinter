import sqlite3
from config import DB_NAME

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with open("database/schema.sql", "r", encoding="utf-8") as f:
        script = f.read()
    conn = get_connection()
    conn.executescript(script)
    conn.commit()
    conn.close()
