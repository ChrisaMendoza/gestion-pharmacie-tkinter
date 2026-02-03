from database.db import get_connection

class PrescriptionsRepository:
    @staticmethod
    def search_medicaments(query: str = "") -> list[tuple]:
        """
        (id, code, nom_commercial, dosage, prix_vente, stock_actuel, date_peremption)
        """
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
        """
        (id, nom, prenom, telephone, email, carte_fidelite)
        """
        p = (phone or "").strip()
        if not p:
            return None
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, nom, prenom, telephone, COALESCE(email,''), COALESCE(carte_fidelite,'')
                FROM clients
                WHERE telephone = ?
                LIMIT 1
            """, (p,))
            return cur.fetchone()
        finally:
            conn.close()

    @staticmethod
    def create_prescription_sale(
        client_id: int,
        ordonnance_info: dict,
        cart_lines: list[dict],
        remise: float = 0.0,
        user_id: int | None = None
    ) -> tuple[int, int]:
        """
        ordonnance_info: {"numero": str, "medecin": str, "date_ordonnance": "YYYY-MM-DD" ou ""}

        cart_lines: [{"medicament_id": int, "nom": str, "quantite": int, "prix_unitaire": float}, ...]

        Enregistre :
        - ordonnances + ordonnance_lignes
        - ventes(type_vente='ORDONNANCE') + vente_lignes
        - update stock + sorties_stock
        Retourne (ordonnance_id, vente_id)
        """
        if not client_id:
            raise ValueError("Un client doit être associé à une ordonnance.")
        if not cart_lines:
            raise ValueError("Ordonnance vide : ajoutez au moins un médicament.")

        try:
            remise = float(remise or 0.0)
        except:
            raise ValueError("Remise invalide.")
        if remise < 0:
            raise ValueError("La remise ne peut pas être négative.")

        numero = (ordonnance_info.get("numero") or "").strip() or None
        medecin = (ordonnance_info.get("medecin") or "").strip() or None
        date_ord = (ordonnance_info.get("date_ordonnance") or "").strip() or None

        # Total brut
        total_brut = 0.0
        for line in cart_lines:
            q = int(line["quantite"])
            pu = float(line["prix_unitaire"])
            if q <= 0:
                raise ValueError("Quantité invalide dans l'ordonnance.")
            if pu < 0:
                raise ValueError("Prix unitaire invalide.")
            total_brut += q * pu

        total_net = max(0.0, total_brut - remise)

        conn = get_connection()
        try:
            cur = conn.cursor()

            # 1) Vérif stock
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

            # 2) Créer ordonnance
            cur.execute("""
                INSERT INTO ordonnances (client_id, numero, medecin, date_ordonnance)
                VALUES (?, ?, ?, ?)
            """, (client_id, numero, medecin, date_ord))
            ordonnance_id = cur.lastrowid

            # 3) Lignes ordonnance
            for line in cart_lines:
                med_id = int(line["medicament_id"])
                q = int(line["quantite"])
                cur.execute("""
                    INSERT INTO ordonnance_lignes (ordonnance_id, medicament_id, quantite)
                    VALUES (?, ?, ?)
                """, (ordonnance_id, med_id, q))

            # 4) Créer vente associée (type ORDONNANCE)
            cur.execute("""
                INSERT INTO ventes (client_id, type_vente, total, remise, user_id)
                VALUES (?, 'ORDONNANCE', ?, ?, ?)
            """, (client_id, total_net, remise, user_id))
            vente_id = cur.lastrowid

            # 5) Vente lignes + stock + sorties_stock
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
                """, (med_id, q, f"VENTE ORDONNANCE #{vente_id} (ORD#{ordonnance_id})"))

            conn.commit()
            return ordonnance_id, vente_id

        except:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def get_prescription_docs_text(ordonnance_id: int, vente_id: int) -> tuple[str, str]:
        """
        Retourne (ticket_txt, facture_txt)
        """
        conn = get_connection()
        try:
            cur = conn.cursor()

            cur.execute("""
                SELECT o.id, COALESCE(o.numero,''), COALESCE(o.medecin,''), COALESCE(o.date_ordonnance,''), o.date_saisie,
                       c.nom, c.prenom, c.telephone, COALESCE(c.email,'')
                FROM ordonnances o
                JOIN clients c ON c.id = o.client_id
                WHERE o.id = ?
            """, (ordonnance_id,))
            o = cur.fetchone()
            if not o:
                raise ValueError("Ordonnance introuvable.")

            (oid, onum, omed, odt, osaisie, cn, cp, ctel, cemail) = o

            cur.execute("""
                SELECT v.id, v.total, v.remise, v.date_vente
                FROM ventes v
                WHERE v.id = ?
            """, (vente_id,))
            v = cur.fetchone()
            if not v:
                raise ValueError("Vente introuvable.")
            (vid, total, remise, dvente) = v

            cur.execute("""
                SELECT m.nom_commercial, vl.quantite, vl.prix_unitaire, vl.sous_total
                FROM vente_lignes vl
                JOIN medicaments m ON m.id = vl.medicament_id
                WHERE vl.vente_id = ?
                ORDER BY m.nom_commercial ASC
            """, (vente_id,))
            lines = cur.fetchall()

            # Ticket
            t = []
            t.append("=== PHARMACIE - TICKET (ORDONNANCE) ===")
            t.append(f"Vente: #{vid}  | Ordonnance: #{oid}")
            if onum:
                t.append(f"Numéro ordonnance: {onum}")
            t.append(f"Date vente: {dvente}")
            t.append(f"Client: {cp} {cn} ({ctel})".strip())
            t.append("----------------------------------------")
            for (nom, q, pu, st) in lines:
                t.append(f"{nom} x{q} @ {pu:.2f}€  = {st:.2f}€")
            t.append("----------------------------------------")
            t.append(f"Remise: {float(remise or 0):.2f}€")
            t.append(f"TOTAL:  {float(total or 0):.2f}€")
            t.append("Merci et à bientôt.")

            # Facture
            f = []
            f.append("=== PHARMACIE - FACTURE (ORDONNANCE) ===")
            f.append(f"Facture vente: #{vid}")
            f.append(f"Ordonnance: #{oid}  | Numéro: {onum}".strip())
            if omed:
                f.append(f"Médecin: {omed}")
            if odt:
                f.append(f"Date ordonnance: {odt}")
            f.append(f"Date vente: {dvente}")
            f.append("")
            f.append("Client :")
            f.append(f"- Nom / Prénom : {cn} {cp}".strip())
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

            return "\n".join(t), "\n".join(f)

        finally:
            conn.close()

    @staticmethod
    def save_docs_to_files(ordonnance_id: int, vente_id: int, folder: str = "docs") -> tuple[str, str]:
        import os
        os.makedirs(folder, exist_ok=True)
        ticket, facture = PrescriptionsRepository.get_prescription_docs_text(ordonnance_id, vente_id)
        ticket_path = os.path.join(folder, f"ticket_ordonnance_{ordonnance_id}_vente_{vente_id}.txt")
        facture_path = os.path.join(folder, f"facture_ordonnance_{ordonnance_id}_vente_{vente_id}.txt")
        with open(ticket_path, "w", encoding="utf-8") as f:
            f.write(ticket)
        with open(facture_path, "w", encoding="utf-8") as f:
            f.write(facture)
        return ticket_path, facture_path
