import sys
import os
from datetime import date

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from database.db import get_connection, init_db, migrate_db
from utils.security import hash_password


def _get_med_id_by_code(cur, code: str) -> int:
    cur.execute("SELECT id FROM medicaments WHERE code=? LIMIT 1", (code,))
    row = cur.fetchone()
    if not row:
        raise ValueError(f"Médicament introuvable pour code='{code}' (seed medicaments manquant ?)")
    return int(row[0])


def _get_client_id_by_phone(cur, phone: str) -> int:
    cur.execute("SELECT id FROM clients WHERE telephone=? LIMIT 1", (phone,))
    row = cur.fetchone()
    if not row:
        raise ValueError(f"Client introuvable pour telephone='{phone}' (seed clients manquant ?)")
    return int(row[0])


def seed():
    # Assure schéma + migrations (ex: date_naissance/secu si tu les as ajoutés)
    init_db()
    try:
        migrate_db()
    except Exception:
        # Si migrate_db n'existe pas encore chez toi, supprime ce try/except et appelle init_db() seulement
        pass

    conn = get_connection()
    cur = conn.cursor()

    # ================= UTILISATEURS =================
    users = [
        ("admin", hash_password("admin123"), "ADMIN", 1),
        ("pharma", hash_password("pharma123"), "PHARMACIEN", 1),
        ("prep", hash_password("prep123"), "PREPARATEUR", 1),
        ("cons", hash_password("cons123"), "CONSEILLER", 1),
    ]
    cur.executemany(
        """
        INSERT OR IGNORE INTO users (username, password_hash, role, actif)
        VALUES (?, ?, ?, ?)
        """,
        users,
    )

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
    cur.executemany(
        """
        INSERT OR IGNORE INTO medicaments
        (code, nom_commercial, categorie, prix_vente, stock_actuel, date_peremption)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        medicaments,
    )

    # ================= CLIENTS =================
    # NB: telephone est NOT NULL UNIQUE dans ton schéma -> obligatoire.
    # Si tu as ajouté date_naissance/secu, ces colonnes seront remplies; sinon SQLite ignorera si elles n'existent pas.
    clients = [
        # nom, prenom, telephone, email, carte_fidelite, date_naissance, secu
        ("Martin", "Sophie", "0612345678", "sophie.martin@test.fr", "FID-0001", "1998-03-14", "298031412345678"),
        ("Durand", "Lucas",  "0698765432", "lucas.durand@test.fr",  "FID-0002", "1987-11-02", "187110212345678"),
        ("Bernard", "Emma",  "0601020304", "emma.bernard@test.fr",  "FID-0003", "2001-07-22", "201072212345678"),
        ("Petit", "Nina",    "0677889900", "",                     "FID-0004", "1994-01-09", "294010912345678"),
        ("Robert", "Hugo",   "0655443322", "hugo.robert@test.fr",   "",         "1990-05-30", "190053012345678"),
    ]

    # Insertion compatible avec schéma (avec ou sans date_naissance/secu)
    # On tente d'insérer avec ces colonnes; si elles n'existent pas encore, on fallback.
    try:
        cur.executemany(
            """
            INSERT OR IGNORE INTO clients
            (nom, prenom, telephone, email, carte_fidelite, date_naissance, secu)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            clients,
        )
    except Exception:
        cur.executemany(
            """
            INSERT OR IGNORE INTO clients
            (nom, prenom, telephone, email, carte_fidelite)
            VALUES (?, ?, ?, ?, ?)
            """,
            [(n, p, t, e, fid) for (n, p, t, e, fid, _dn, _secu) in clients],
        )

    # ================= ORDONNANCES + LIGNES =================
    # On crée quelques ordonnances en liant des médicaments par code.
    today = date.today().isoformat()

    # Récup ids clients
    c1 = _get_client_id_by_phone(cur, "0612345678")
    c2 = _get_client_id_by_phone(cur, "0698765432")
    c3 = _get_client_id_by_phone(cur, "0601020304")

    ordonnances = [
        (c1, "ORD-2026-001", "Dr Lemoine", today),
        (c2, "ORD-2026-002", "Dr Nguyen",  today),
        (c3, "ORD-2026-003", "Dr Benali",  today),
    ]
    cur.executemany(
        """
        INSERT INTO ordonnances (client_id, numero, medecin, date_ordonnance)
        VALUES (?, ?, ?, ?)
        """,
        ordonnances,
    )

    # Récup ids ordonnances insérées (les 3 dernières)
    cur.execute("SELECT id, numero FROM ordonnances ORDER BY id DESC LIMIT 3")
    last3 = list(reversed(cur.fetchall()))
    ord_id_by_num = {num: oid for (oid, num) in last3}

    # Médicaments ids
    dol = _get_med_id_by_code(cur, "DOLI500")
    ibu = _get_med_id_by_code(cur, "IBU200")
    amx = _get_med_id_by_code(cur, "AMOX1G")
    ven = _get_med_id_by_code(cur, "VENTO")
    sme = _get_med_id_by_code(cur, "SMECT")

    ordonnance_lignes = [
        # ordonnance_id, medicament_id, quantite
        (ord_id_by_num["ORD-2026-001"], dol, 1),
        (ord_id_by_num["ORD-2026-001"], ibu, 1),

        (ord_id_by_num["ORD-2026-002"], amx, 1),
        (ord_id_by_num["ORD-2026-002"], sme, 2),

        (ord_id_by_num["ORD-2026-003"], ven, 1),
        (ord_id_by_num["ORD-2026-003"], dol, 2),
    ]
    cur.executemany(
        """
        INSERT INTO ordonnance_lignes (ordonnance_id, medicament_id, quantite)
        VALUES (?, ?, ?)
        """,
        ordonnance_lignes,
    )

    conn.commit()
    conn.close()
    print("Seed OK: utilisateurs + medicaments + clients + ordonnances (+ lignes).")


if __name__ == "__main__":
    seed()
