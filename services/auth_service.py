from database.db import get_connection
from utils.security import hash_password
from utils.logger import log_action


def authenticate(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, password_hash, role, actif FROM users WHERE username=?",
        (username,)
    )
    user = cursor.fetchone()
    conn.close()

    if not user:
        raise ValueError("Utilisateur inexistant")
    if user[3] == 0:
        raise PermissionError("Compte désactivé")
    if hash_password(password) != user[1]:
        raise ValueError("Mot de passe incorrect")

    log_action(user[0], "Connexion")

    role = (user[2] or "").strip().upper()
    return {"id": user[0], "role": role}
