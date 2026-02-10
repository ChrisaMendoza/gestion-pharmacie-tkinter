from datetime import datetime
from database.db import get_connection


class SalesRepository:
    @staticmethod
    def search_medicaments(query: str = "") -> list[tuple]:
        q = (query or "").strip()
        conn = get_connection()
        try:
            cur = conn.cursor()
            if not q:
                cur.execute("""
                            SELECT id, code, nom_commercial, COALESCE(dosage,''), COALESCE(prix_vente,0), COALESCE(stock_actuel,0), COALESCE(date_peremption,'')
                            FROM medicaments
                            ORDER BY nom_commercial ASC
                                LIMIT 200
                            """)
            else:
                like = f"%{q}%"
                cur.execute("""
                            SELECT id, code, nom_commercial, COALESCE(dosage,''), COALESCE(prix_vente,0), COALESCE(stock_actuel,0), COALESCE(date_peremption,'')
                            FROM medicaments
                            WHERE code LIKE ? OR nom_commercial LIKE ? OR nom_generique LIKE ? OR categorie LIKE ?
                            ORDER BY nom_commercial ASC
                                LIMIT 200
                            """, (like, like, like, like))
            return cur.fetchall()
        finally:
            conn.close()

    @staticmethod
    def find_client_by_phone(phone: str) -> tuple | None:
        p = (phone or "").strip()
        if not p:
            return None
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                        SELECT id, nom, prenom, telephone
                        FROM clients
                        WHERE telephone = ?
                            LIMIT 1
                        """, (p,))
            return cur.fetchone()
        finally:
            conn.close()

    @staticmethod
    def create_sale(cart_lines: list[dict], remise: float = 0.0, client_id: int | None = None, user_id: int | None = None) -> int:
        if not cart_lines:
            raise ValueError("Panier vide : ajoutez au moins un médicament.")

        try:
            remise = float(remise or 0.0)
        except Exception:
            raise ValueError("Remise invalide.")
        if remise < 0:
            raise ValueError("La remise ne peut pas être négative.")

        total_brut = 0.0
        for line in cart_lines:
            q = int(line["quantite"])
            pu = float(line["prix_unitaire"])
            if q <= 0:
                raise ValueError("Quantité invalide dans le panier.")
            if pu < 0:
                raise ValueError("Prix unitaire invalide.")
            total_brut += q * pu

        total_net = max(0.0, total_brut - remise)

        conn = get_connection()
        try:
            cur = conn.cursor()

            # Vérif stock
            for line in cart_lines:
                med_id = int(line["medicament_id"])
                q = int(line["quantite"])
                cur.execute("SELECT stock_actuel, nom_commercial FROM medicaments WHERE id=?", (med_id,))
                row = cur.fetchone()
                if not row:
                    raise ValueError(f"Médicament introuvable (id={med_id}).")
                stock, nom = row
                stock = int(stock or 0)
                if q > stock:
                    raise ValueError(f"Stock insuffisant pour '{nom}' : demandé {q}, disponible {stock}.")

            # Création vente
            cur.execute("""
                        INSERT INTO ventes (client_id, type_vente, total, remise, user_id)
                        VALUES (?, 'LIBRE', ?, ?, ?)
                        """, (client_id, total_net, remise, user_id))
            vente_id = cur.lastrowid

            # Lignes + stock + sorties_stock
            for line in cart_lines:
                med_id = int(line["medicament_id"])
                q = int(line["quantite"])
                pu = float(line["prix_unitaire"])
                sous_total = q * pu

                cur.execute("""
                            INSERT INTO vente_lignes (vente_id, medicament_id, quantite, prix_unitaire, sous_total)
                            VALUES (?, ?, ?, ?, ?)
                            """, (vente_id, med_id, q, pu, sous_total))

                cur.execute("""
                            UPDATE medicaments
                            SET stock_actuel = stock_actuel - ?
                            WHERE id = ?
                            """, (q, med_id))

                cur.execute("""
                            INSERT INTO sorties_stock (medicament_id, quantite, motif)
                            VALUES (?, ?, ?)
                            """, (med_id, q, f"VENTE LIBRE #{vente_id}"))

            conn.commit()
            return vente_id
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def get_sale_ticket_text(vente_id: int) -> str:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                        SELECT v.id, v.type_vente, v.total, v.remise, v.date_vente,
                               COALESCE(c.nom,''), COALESCE(c.prenom,''), COALESCE(c.telephone,'')
                        FROM ventes v
                                 LEFT JOIN clients c ON c.id = v.client_id
                        WHERE v.id = ?
                        """, (vente_id,))
            header = cur.fetchone()
            if not header:
                raise ValueError("Vente introuvable.")

            (vid, type_vente, total, remise, date_vente, cn, cp, ctel) = header

            cur.execute("""
                        SELECT m.nom_commercial, vl.quantite, vl.prix_unitaire, vl.sous_total
                        FROM vente_lignes vl
                                 JOIN medicaments m ON m.id = vl.medicament_id
                        WHERE vl.vente_id = ?
                        ORDER BY m.nom_commercial ASC
                        """, (vente_id,))
            lines = cur.fetchall()

            parts = []
            parts.append("=== PHARMACIE - TICKET DE CAISSE ===")
            parts.append(f"Vente: #{vid} ({type_vente})")
            parts.append(f"Date: {date_vente}")
            if ctel:
                parts.append(f"Client: {cp} {cn} ({ctel})".strip())
            parts.append("------------------------------------")
            for (nom, q, pu, st) in lines:
                parts.append(f"{nom} x{q} @ {pu:.2f}€  = {st:.2f}€")
            parts.append("------------------------------------")
            parts.append(f"Remise: {float(remise or 0):.2f}€")
            parts.append(f"TOTAL:  {float(total or 0):.2f}€")
            parts.append("Merci et à bientôt.")
            return "\n".join(parts)
        finally:
            conn.close()

    @staticmethod
    def save_ticket_to_file(vente_id: int, folder: str = "tickets") -> str:
        import os
        os.makedirs(folder, exist_ok=True)
        text = SalesRepository.get_sale_ticket_text(vente_id)
        filename = os.path.join(folder, f"ticket_vente_{vente_id}.txt")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(text)
        return filename

    @staticmethod
    def get_sale_invoice_text(vente_id: int) -> str:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                        SELECT v.id, v.type_vente, v.total, v.remise, v.date_vente,
                               COALESCE(c.nom,''), COALESCE(c.prenom,''), COALESCE(c.telephone,''), COALESCE(c.email,'')
                        FROM ventes v
                                 LEFT JOIN clients c ON c.id = v.client_id
                        WHERE v.id = ?
                        """, (vente_id,))
            header = cur.fetchone()
            if not header:
                raise ValueError("Vente introuvable.")

            (vid, type_vente, total, remise, date_vente, cn, cp, ctel, cemail) = header

            cur.execute("""
                        SELECT m.nom_commercial, vl.quantite, vl.prix_unitaire, vl.sous_total
                        FROM vente_lignes vl
                                 JOIN medicaments m ON m.id = vl.medicament_id
                        WHERE vl.vente_id = ?
                        ORDER BY m.nom_commercial ASC
                        """, (vente_id,))
            lines = cur.fetchall()

            f = []
            f.append("=== PHARMACIE - FACTURE ===")
            f.append(f"Vente: #{vid} ({type_vente})")
            f.append(f"Date: {date_vente}")
            if ctel or cn or cp:
                f.append("Client :")
                f.append(f"- Nom / Prénom : {cn} {cp}".strip())
                if ctel:
                    f.append(f"- Téléphone : {ctel}")
                if cemail:
                    f.append(f"- Email : {cemail}")
            f.append("")
            f.append("Détails :")
            for (nom, q, pu, st) in lines:
                f.append(f"- {nom} | Qté: {q} | PU: {pu:.2f}€ | Sous-total: {st:.2f}€")
            f.append("")
            f.append(f"Remise: {float(remise or 0):.2f}€")
            f.append(f"TOTAL À PAYER: {float(total or 0):.2f}€")
            return "\n".join(f)
        finally:
            conn.close()

    @staticmethod
    def save_invoice_to_file(vente_id: int, folder: str = "docs") -> str:
        import os
        os.makedirs(folder, exist_ok=True)
        text = SalesRepository.get_sale_invoice_text(vente_id)
        filename = os.path.join(folder, f"facture_vente_{vente_id}.txt")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(text)
        return filename
