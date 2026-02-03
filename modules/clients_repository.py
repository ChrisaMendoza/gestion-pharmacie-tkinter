from database.db import get_connection
from modules.validators import require, clean_str, normalize_phone, is_valid_email, is_valid_phone_fr

class ClientsRepository:
    @staticmethod
    def add_client(nom: str, prenom: str, telephone: str, email: str = None, carte_fidelite: str = None) -> int:
        nom = require(nom, "Nom")
        prenom = require(prenom, "Prénom")
        telephone_raw = require(telephone, "Téléphone")
        telephone_norm = normalize_phone(telephone_raw)

        if not is_valid_phone_fr(telephone_norm):
            raise ValueError("Téléphone invalide. Format attendu : 0XXXXXXXXX (10 chiffres).")

        email = clean_str(email)
        if not is_valid_email(email):
            raise ValueError("Email invalide.")

        carte_fidelite = clean_str(carte_fidelite) or None

        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO clients (nom, prenom, telephone, email, carte_fidelite)
                VALUES (?, ?, ?, ?, ?)
                """,
                (nom, prenom, telephone_norm, email or None, carte_fidelite),
            )
            conn.commit()
            return cur.lastrowid
        except Exception as e:
            conn.rollback()
            if "UNIQUE" in str(e).upper():
                raise ValueError("Un client existe déjà avec ce numéro de téléphone.")
            raise
        finally:
            conn.close()

    @staticmethod
    def update_client(client_id: int, nom: str, prenom: str, telephone: str, email: str = None, carte_fidelite: str = None) -> None:
        if not client_id:
            raise ValueError("Client non sélectionné.")

        nom = require(nom, "Nom")
        prenom = require(prenom, "Prénom")
        telephone_raw = require(telephone, "Téléphone")
        telephone_norm = normalize_phone(telephone_raw)

        if not is_valid_phone_fr(telephone_norm):
            raise ValueError("Téléphone invalide. Format attendu : 0XXXXXXXXX (10 chiffres).")

        email = clean_str(email)
        if not is_valid_email(email):
            raise ValueError("Email invalide.")

        carte_fidelite = clean_str(carte_fidelite) or None

        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE clients
                SET nom=?, prenom=?, telephone=?, email=?, carte_fidelite=?
                WHERE id=?
                """,
                (nom, prenom, telephone_norm, email or None, carte_fidelite, client_id),
            )
            if cur.rowcount == 0:
                raise ValueError("Client introuvable (id invalide).")
            conn.commit()
        except Exception as e:
            conn.rollback()
            if "UNIQUE" in str(e).upper():
                raise ValueError("Un client existe déjà avec ce numéro de téléphone.")
            raise
        finally:
            conn.close()

    @staticmethod
    def delete_client(client_id: int) -> None:
        if not client_id:
            raise ValueError("Client non sélectionné.")
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM clients WHERE id=?", (client_id,))
            if cur.rowcount == 0:
                raise ValueError("Client introuvable.")
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def search_clients(query: str = "") -> list[tuple]:
        q = (query or "").strip()
        conn = get_connection()
        try:
            cur = conn.cursor()
            if not q:
                cur.execute("""
                    SELECT id, nom, prenom, telephone, COALESCE(email,''), COALESCE(carte_fidelite,'')
                    FROM clients
                    ORDER BY date_creation DESC
                    LIMIT 200
                """)
            else:
                like = f"%{q}%"
                cur.execute("""
                    SELECT id, nom, prenom, telephone, COALESCE(email,''), COALESCE(carte_fidelite,'')
                    FROM clients
                    WHERE nom LIKE ? OR prenom LIKE ? OR telephone LIKE ? OR email LIKE ? OR carte_fidelite LIKE ?
                    ORDER BY nom ASC, prenom ASC
                    LIMIT 200
                """, (like, like, like, like, like))
            return cur.fetchall()
        finally:
            conn.close()

    @staticmethod
    def get_client_history(client_id: int) -> dict:
        if not client_id:
            raise ValueError("Client non sélectionné.")

        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, type_vente, total, remise, date_vente
                FROM ventes
                WHERE client_id=?
                ORDER BY date_vente DESC
                LIMIT 200
            """, (client_id,))
            ventes = cur.fetchall()

            cur.execute("""
                SELECT o.id, COALESCE(o.numero,''), COALESCE(o.medecin,''), COALESCE(o.date_ordonnance,''), o.date_saisie
                FROM ordonnances o
                WHERE o.client_id=?
                ORDER BY o.date_saisie DESC
                LIMIT 200
            """, (client_id,))
            ordonnances = cur.fetchall()

            return {"ventes": ventes, "ordonnances": ordonnances}
        finally:
            conn.close()
