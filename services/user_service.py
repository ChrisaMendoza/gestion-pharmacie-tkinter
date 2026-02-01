from database.db import get_connection
from utils.security import hash_password

def create_user(data):
    conn = get_connection()
    try:
        conn.execute("""
                     INSERT INTO users
                         (username, password_hash, role, nom, prenom, email, actif)
                     VALUES (?, ?, ?, ?, ?, ?, 1)
                     """, (
                         data["username"],
                         hash_password(data["password"]),
                         data["role"],
                         data.get("nom"),
                         data.get("prenom"),
                         data.get("email")
                     ))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
