from database.db import get_connection
from datetime import datetime

# ================= ENTRÉE DE STOCK =================
def entree_stock(medicament_id, quantite, prix_vente, date_peremption):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
                UPDATE medicaments
                SET stock_actuel = stock_actuel + ?,
                    prix_vente = ?,
                    date_peremption = ?
                WHERE id = ?
                """, (quantite, prix_vente, date_peremption, medicament_id))

    conn.commit()
    conn.close()


# ================= SORTIE DE STOCK (GESTION) =================
def sortie_stock(medicament_id, quantite):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT stock_actuel FROM medicaments WHERE id=?", (medicament_id,))
    row = cur.fetchone()

    if not row:
        conn.close()
        raise ValueError("Médicament introuvable")

    stock = row[0]
    if quantite > stock:
        conn.close()
        raise ValueError("Stock insuffisant")

    cur.execute("""
                UPDATE medicaments
                SET stock_actuel = stock_actuel - ?
                WHERE id = ?
                """, (quantite, medicament_id))

    conn.commit()
    conn.close()


# ================= SORTIE DE STOCK (VENTE) =================
def sortie_stock_vente(medicament_id, quantite):
    sortie_stock(medicament_id, quantite)


# ================= TOUS LES MÉDICAMENTS (STOCK) =================
def get_all_stocks():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
                SELECT id, code, nom_commercial, prix_vente,
                       stock_actuel, date_peremption
                FROM medicaments
                ORDER BY nom_commercial
                """)

    rows = cur.fetchall()
    conn.close()
    return rows


# ================= MÉDICAMENTS DISPONIBLES À LA VENTE =================
def get_medicaments_for_sale():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
                SELECT id, code, nom_commercial, prix_vente, stock_actuel
                FROM medicaments
                WHERE stock_actuel > 0
                ORDER BY nom_commercial
                """)

    rows = cur.fetchall()
    conn.close()
    return rows
