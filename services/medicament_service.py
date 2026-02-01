from database.db import get_connection

def get_medicament_details(code):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
                SELECT
                    code,
                    nom_commercial,
                    categorie,
                    prix_vente,
                    stock_actuel,
                    seuil_alerte,
                    date_peremption
                FROM medicaments
                WHERE code = ?
                """, (code,))
    row = cur.fetchone()
    conn.close()
    return row

from database.db import get_connection

def get_medicament_details_by_id(med_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
                SELECT code, nom_commercial, categorie, prix_vente,
                       stock_actuel, seuil_alerte, date_peremption
                FROM medicaments
                WHERE id = ?
                """, (med_id,))
    row = cur.fetchone()
    conn.close()
    return row

def add_medicament(data):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
                INSERT INTO medicaments
                (code, nom_commercial, categorie, prix_vente, stock_actuel, date_peremption)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    data["code"],
                    data["nom"],
                    data["categorie"],
                    data["prix"],
                    data["stock"],
                    data["peremption"]
                ))

    conn.commit()
    conn.close()

def get_medicament_by_id(med_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
                SELECT id, code, nom_commercial, categorie, prix_vente, stock_actuel, date_peremption
                FROM medicaments
                WHERE id = ?
                """, (med_id,))
    row = cur.fetchone()
    conn.close()
    return row


def update_medicament(med_id, data):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
                UPDATE medicaments
                SET code = ?,
                    nom_commercial = ?,
                    categorie = ?,
                    prix_vente = ?,
                    stock_actuel = ?,
                    date_peremption = ?
                WHERE id = ?
                """, (
                    data["code"],
                    data["nom"],
                    data["categorie"],
                    data["prix"],
                    data["stock"],
                    data["peremption"],
                    med_id
                ))
    conn.commit()
    conn.close()