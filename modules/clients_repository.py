import re
from datetime import datetime

from database.db import get_connection
from modules.validators import require, clean_str, normalize_phone, is_valid_email, is_valid_phone_fr


class ClientsRepository:
    @staticmethod
    def _normalize_date_yyyy_mm_dd(value: str) -> str | None:
        v = clean_str(value)
        if not v:
            return None
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except Exception:
            raise ValueError("Date de naissance invalide. Format attendu : YYYY-MM-DD.")
        return v

    @staticmethod
    def _normalize_secu(value: str) -> str | None:
        v = clean_str(value)
        v = re.sub(r"\s+", "", v)
        if not v:
            return None
        if not re.fullmatch(r"\d{13}(\d{2})?", v):
            raise ValueError("Numéro de sécurité sociale invalide (13 ou 15 chiffres).")
        return v

    @staticmethod
    def find_client_by_secu(secu: str) -> tuple | None:
        s = ClientsRepository._normalize_secu(secu)
        if not s:
            return None
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, nom, prenom, COALESCE(telephone,''), COALESCE(email,''), COALESCE(carte_fidelite,''),
                       COALESCE(date_naissance,''), COALESCE(secu,'')
                FROM clients
                WHERE secu = ?
                    LIMIT 1
                """,
                (s,),
            )
            return cur.fetchone()
        finally:
            conn.close()

    @staticmethod
    def add_client(
            nom: str,
            prenom: str,
            telephone: str,
            email: str = None,
            carte_fidelite: str = None,
            date_naissance: str = None,
            secu: str = None,
    ) -> int:
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

        date_n = ClientsRepository._normalize_date_yyyy_mm_dd(date_naissance)
        secu_n = ClientsRepository._normalize_secu(secu)

        conn = get_connection()
        try:
            cur = conn.cursor()

            if secu_n:
                cur.execute("SELECT id FROM clients WHERE secu = ? LIMIT 1", (secu_n,))
                if cur.fetchone():
                    raise ValueError("Un client existe déjà avec ce numéro de sécurité sociale.")

            cur.execute(
                """
                INSERT INTO clients (nom, prenom, telephone, email, carte_fidelite, date_naissance, secu)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (nom, prenom, telephone_norm, email or None, carte_fidelite, date_n, secu_n),
            )
            conn.commit()
            return cur.lastrowid
        except Exception as e:
            conn.rollback()
            if "UNIQUE" in str(e).upper():
                msg = str(e).upper()
                if "TELEPHONE" in msg:
                    raise ValueError("Un client existe déjà avec ce numéro de téléphone.")
                if "SECU" in msg or "IDX_CLIENTS_SECU_UNIQUE" in msg:
                    raise ValueError("Un client existe déjà avec ce numéro de sécurité sociale.")
            raise
        finally:
            conn.close()

    @staticmethod
    def update_client(
            client_id: int,
            nom: str,
            prenom: str,
            telephone: str,
            email: str = None,
            carte_fidelite: str = None,
            date_naissance: str = None,
            secu: str = None,
    ) -> None:
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

        date_n = ClientsRepository._normalize_date_yyyy_mm_dd(date_naissance)
        secu_n = ClientsRepository._normalize_secu(secu)

        conn = get_connection()
        try:
            cur = conn.cursor()

            if secu_n:
                cur.execute("SELECT id FROM clients WHERE secu = ? AND id <> ? LIMIT 1", (secu_n, client_id))
                if cur.fetchone():
                    raise ValueError("Un autre client existe déjà avec ce numéro de sécurité sociale.")

            cur.execute(
                """
                UPDATE clients
                SET nom=?, prenom=?, telephone=?, email=?, carte_fidelite=?, date_naissance=?, secu=?
                WHERE id=?
                """,
                (nom, prenom, telephone_norm, email or None, carte_fidelite, date_n, secu_n, client_id),
            )
            if cur.rowcount == 0:
                raise ValueError("Client introuvable (id invalide).")
            conn.commit()
        except Exception as e:
            conn.rollback()
            if "UNIQUE" in str(e).upper():
                msg = str(e).upper()
                if "TELEPHONE" in msg:
                    raise ValueError("Un client existe déjà avec ce numéro de téléphone.")
                if "SECU" in msg or "IDX_CLIENTS_SECU_UNIQUE" in msg:
                    raise ValueError("Un client existe déjà avec ce numéro de sécurité sociale.")
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
                cur.execute(
                    """
                    SELECT id, nom, prenom, telephone, COALESCE(email,''), COALESCE(carte_fidelite,''),
                           COALESCE(date_naissance,''), COALESCE(secu,'')
                    FROM clients
                    ORDER BY date_creation DESC
                        LIMIT 200
                    """
                )
            else:
                like = f"%{q}%"
                cur.execute(
                    """
                    SELECT id, nom, prenom, telephone, COALESCE(email,''), COALESCE(carte_fidelite,''),
                           COALESCE(date_naissance,''), COALESCE(secu,'')
                    FROM clients
                    WHERE nom LIKE ?
                       OR prenom LIKE ?
                       OR telephone LIKE ?
                       OR email LIKE ?
                       OR carte_fidelite LIKE ?
                       OR secu LIKE ?
                    ORDER BY nom ASC, prenom ASC
                        LIMIT 200
                    """,
                    (like, like, like, like, like, like),
                )
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
            cur.execute(
                """
                SELECT id, type_vente, total, remise, date_vente
                FROM ventes
                WHERE client_id=?
                ORDER BY date_vente DESC
                    LIMIT 200
                """,
                (client_id,),
            )
            ventes = cur.fetchall()

            cur.execute(
                """
                SELECT o.id, COALESCE(o.numero,''), COALESCE(o.medecin,''), COALESCE(o.date_ordonnance,''), o.date_saisie
                FROM ordonnances o
                WHERE o.client_id=?
                ORDER BY o.date_saisie DESC
                    LIMIT 200
                """,
                (client_id,),
            )
            ordonnances = cur.fetchall()

            return {"ventes": ventes, "ordonnances": ordonnances}
        finally:
            conn.close()
