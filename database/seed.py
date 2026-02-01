import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from database.db import get_connection
from utils.security import hash_password

def seed():
    conn = get_connection()
    cur = conn.cursor()

    # ================= UTILISATEURS =================
    users = [
        ("admin", hash_password("admin123"), "ADMIN", 1),
        ("pharma", hash_password("pharma123"), "PHARMACIEN", 1),
        ("prep", hash_password("prep123"), "PREPARATEUR", 1),
        ("cons", hash_password("cons123"), "CONSEILLER", 1),
    ]

    cur.executemany("""
                    INSERT OR IGNORE INTO users (username, password_hash, role, actif)
        VALUES (?, ?, ?, ?)
                    """, users)

    # ================= MEDICAMENTS =================
    medicaments = [
        ("DOLI500", "Doliprane 500 mg", "Antalgique", 2.10, 120, "2027-06-30"),
        ("DOLI1G", "Doliprane 1 g", "Antalgique", 2.90, 90, "2027-04-15"),
        ("PARA500", "Paracétamol 500 mg", "Antalgique", 1.80, 150, "2026-12-31"),
        ("IBU200", "Ibuprofène 200 mg", "Anti-inflammatoire", 3.20, 60, "2025-11-20"),
        ("IBU400", "Ibuprofène 400 mg", "Anti-inflammatoire", 4.50, 40, "2025-09-10"),
        ("AMOX1G", "Amoxicilline 1 g", "Antibiotique", 6.80, 25, "2025-03-01"),
        ("AUG875", "Augmentin 875/125", "Antibiotique", 9.40, 20, "2025-02-15"),
        ("VENTO", "Ventoline", "Respiratoire", 8.90, 30, "2026-01-01"),
        ("SMECT", "Smecta", "Digestif", 5.60, 70, "2027-08-01"),
        ("GAVIS", "Gaviscon", "Digestif", 6.20, 50, "2026-05-01"),
        ("SPASF", "Spasfon", "Antispasmodique", 4.80, 45, "2026-04-01"),
        ("IMOD", "Imodium", "Antidiarrhéique", 5.90, 35, "2025-10-01"),
        ("CLARI", "Claritine", "Antihistaminique", 6.90, 55, "2026-03-15"),
        ("LEVOTH", "Levothyrox", "Hormone", 3.10, 80, "2027-01-01"),
        ("EFFER", "Efferalgan", "Antalgique", 3.00, 85, "2026-06-01"),
        ("ASPIR", "Aspirine UPSA", "Antalgique", 2.80, 95, "2026-09-01"),
        ("VITC", "Vitamine C UPSA", "Complément", 4.50, 130, "2028-01-01"),
    ]

    cur.executemany("""
                    INSERT OR IGNORE INTO medicaments
        (code, nom_commercial, categorie, prix_vente, stock_actuel, date_peremption)
        VALUES (?, ?, ?, ?, ?, ?)
                    """, medicaments)

    conn.commit()
    conn.close()
    print("Base de données initialisée (utilisateurs + médicaments).")

if __name__ == "__main__":
    seed()
