from database.db import get_connection

class StatsRepository:
    @staticmethod
    def chiffre_affaires(period: str = "jour"):
        """
        period = 'jour' | 'mois' | 'annee'
        Retour: [(periode, chiffre_affaires), ...]
        """
        fmt_map = {"jour": "%Y-%m-%d", "mois": "%Y-%m", "annee": "%Y"}
        if period not in fmt_map:
            raise ValueError("Période invalide. Utilisez 'jour', 'mois' ou 'annee'.")

        fmt = fmt_map[period]
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(f"""
                SELECT strftime('{fmt}', date_vente) AS periode,
                       COALESCE(SUM(total), 0) AS chiffre_affaires
                FROM ventes
                GROUP BY periode
                ORDER BY periode ASC
            """)
            return cur.fetchall()
        finally:
            conn.close()

    @staticmethod
    def medicaments_plus_vendus(limit: int = 10):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT m.nom_commercial, COALESCE(SUM(vl.quantite),0) AS total_vendu
                FROM vente_lignes vl
                JOIN medicaments m ON m.id = vl.medicament_id
                GROUP BY m.id
                ORDER BY total_vendu DESC
                LIMIT ?
            """, (limit,))
            return cur.fetchall()
        finally:
            conn.close()

    @staticmethod
    def entrees_stock(period: str = "jour"):
        fmt_map = {"jour": "%Y-%m-%d", "mois": "%Y-%m", "annee": "%Y"}
        fmt = fmt_map.get(period, "%Y-%m-%d")
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(f"""
                SELECT strftime('{fmt}', e.date_entree) AS periode,
                       COALESCE(SUM(e.quantite),0) AS total_entrees
                FROM entrees_stock e
                GROUP BY periode
                ORDER BY periode ASC
            """)
            return cur.fetchall()
        finally:
            conn.close()

    @staticmethod
    def sorties_stock(period: str = "jour"):
        fmt_map = {"jour": "%Y-%m-%d", "mois": "%Y-%m", "annee": "%Y"}
        fmt = fmt_map.get(period, "%Y-%m-%d")
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(f"""
                SELECT strftime('{fmt}', s.date_sortie) AS periode,
                       COALESCE(SUM(s.quantite),0) AS total_sorties
                FROM sorties_stock s
                GROUP BY periode
                ORDER BY periode ASC
            """)
            return cur.fetchall()
        finally:
            conn.close()

    @staticmethod
    def medicaments_proches_peremption(jours: int = 30):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT nom_commercial, date_peremption
                FROM medicaments
                WHERE date_peremption IS NOT NULL
                  AND date(date_peremption) <= date('now', ?)
                ORDER BY date_peremption ASC
            """, (f"+{jours} days",))
            return cur.fetchall()
        finally:
            conn.close()

    @staticmethod
    def clients_fideles(limit: int = 10):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT c.nom, c.prenom, COUNT(v.id) AS nb_achats
                FROM ventes v
                JOIN clients c ON c.id = v.client_id
                GROUP BY c.id
                ORDER BY nb_achats DESC
                LIMIT ?
            """, (limit,))
            return cur.fetchall()
        finally:
            conn.close()
