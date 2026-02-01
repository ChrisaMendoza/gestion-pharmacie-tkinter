import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from database.db import get_connection

def seed():
    conn = get_connection()
    cur = conn.cursor()

    medicaments = [
        ("DOLI500", "Doliprane 500 mg", "Antalgique", 2.10, 120, 20, "2027-06-30"),
        ("DOLI1G", "Doliprane 1000 mg", "Antalgique", 2.90, 90, 20, "2027-04-15"),
        ("PARA500", "Paracétamol 500 mg", "Antalgique", 1.80, 150, 30, "2026-12-31"),
        ("IBU200", "Ibuprofène 200 mg", "Anti-inflammatoire", 3.20, 60, 15, "2025-11-20"),
        ("IBU400", "Ibuprofène 400 mg", "Anti-inflammatoire", 4.50, 40, 15, "2025-09-10"),
        ("AMOX1G", "Amoxicilline 1 g", "Antibiotique", 6.80, 25, 10, "2025-03-01"),
        ("AUG875", "Augmentin 875/125", "Antibiotique", 9.40, 20, 10, "2025-02-15"),
        ("VENTO", "Ventoline", "Respiratoire", 8.90, 30, 10, "2026-01-01"),
        ("SMECT", "Smecta", "Digestif", 5.60, 70, 15, "2027-08-01"),
        ("GAVIS", "Gaviscon", "Digestif", 6.20, 50, 15, "2026-05-01"),
        ("SPASF", "Spasfon", "Antispasmodique", 4.80, 45, 15, "2026-04-01"),
        ("IMOD", "Imodium", "Antidiarrhéique", 5.90, 35, 10, "2025-10-01"),
        ("XYZAL", "Xyzall", "Antihistaminique", 7.10, 40, 10, "2026-02-01"),
        ("CLARI", "Claritine", "Antihistaminique", 6.90, 55, 15, "2026-03-15"),
        ("LEVOTH", "Levothyrox", "Hormone", 3.10, 80, 20, "2027-01-01"),
        ("INS100", "Insuline Rapide", "Hormone", 29.00, 15, 5, "2024-12-20"),
        ("DAFAL", "Dafalgan", "Antalgique", 2.50, 100, 20, "2027-07-01"),
        ("EFFER", "Efferalgan", "Antalgique", 3.00, 85, 20, "2026-06-01"),
        ("ASPIR", "Aspirine UPSA", "Antalgique", 2.80, 95, 20, "2026-09-01"),
        ("VITC", "Vitamine C UPSA", "Complément", 4.50, 130, 30, "2028-01-01")
    ]

    cur.execute("UPDATE medicaments SET stock_actuel = 0 WHERE code IN ('INS100','AMOX1G')")

    cur.execute("""
                UPDATE medicaments
                SET date_peremption = '2023-12-31'
                WHERE code IN ('INS100', 'AMOX1G')
                """)

    cur.executemany("""
                    INSERT OR IGNORE INTO medicaments
        (code, nom_commercial, categorie, prix_vente, stock_actuel, seuil_alerte, date_peremption)
        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, medicaments)

    conn.commit()
    conn.close()
    print("Base de données peuplée avec de vrais médicaments.")

if __name__ == "__main__":
    seed()
