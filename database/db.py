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


import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def create_default_users():
    conn = get_connection()
    cursor = conn.cursor()

    users = [
        ("admin", hash_password("admin123"), "Admin", "Admin", "", ""),
        ("pharmacie", hash_password("pharma123"), "Pharmacien", "User", "", ""),
        ("preparateur", hash_password("prep123"), "Preparateur", "User", "", ""),
        ("conseiller", hash_password("cons123"), "Conseiller", "User", "", "")
    ]

    for user in users:
        cursor.execute("""
                       INSERT OR IGNORE INTO users
            (username, password_hash, role, nom, prenom, email)
            VALUES (?, ?, ?, ?, ?, ?)
                       """, user)

    conn.commit()
    conn.close()
