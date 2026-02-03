import tkinter as tk
from tkinter import ttk, messagebox

from modules.prescriptions_repository import PrescriptionsRepository

class PrescriptionsFrame(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.cart = []
        self.client_id = None
        self.client_label_var = tk.StringVar(value="Client : (non associé)")
        self.last_ids = None  # (ordonnance_id, vente_id)

        self._build_ui()
        self.refresh_medicaments()
        self.refresh_cart()

    def _build_ui(self):
        top = ttk.LabelFrame(self, text="Informations ordonnance + client (obligatoire)")
        top.pack(fill="x", padx=10, pady=10)

        row1 = ttk.Frame(top)
        row1.pack(fill="x", padx=8, pady=6)

        ttk.Label(row1, text="Téléphone client :").pack(side="left")
        self.client_phone_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self.client_phone_var, width=18).pack(side="left", padx=6)
        ttk.Button(row1, text="Rechercher client", command=self.attach_client).pack(side="left")

        ttk.Label(row1, textvariable=self.client_label_var).pack(side="left", padx=(15, 0))

        row2 = ttk.Frame(top)
        row2.pack(fill="x", padx=8, pady=6)

        ttk.Label(row2, text="Numéro ordonnance (optionnel) :").pack(side="left")
        self.numero_var = tk.StringVar()
        ttk.Entry(row2, textvariable=self.numero_var, width=18).pack(side="left", padx=6)

        ttk.Label(row2, text="Médecin (optionnel) :").pack(side="left", padx=(15, 0))
        self.medecin_var = tk.StringVar()
        ttk.Entry(row2, textvariable=self.medecin_var, width=24).pack(side="left", padx=6)

        ttk.Label(row2, text="Date ordonnance (YYYY-MM-DD, optionnel) :").pack(side="left", padx=(15, 0))
        self.date_var = tk.StringVar()
        ttk.Entry(row2, textvariable=self.date_var, width=14).pack(side="left", padx=6)

        # ===== Medicaments + cart =====
        main = ttk.Frame(self)
        main.pack(fill="both", expand=True, padx=10, pady=5)

        left = ttk.LabelFrame(main, text="Médicaments")
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        search_bar = ttk.Frame(left)
        search_bar.pack(fill="x", padx=8, pady=8)

        ttk.Label(search_bar, text="Recherche :").pack(side="left")
        self.med_search_var = tk.StringVar()
        e = ttk.Entry(search_bar, textvariable=self.med_search_var, width=35)
        e.pack(side="left", padx=8)
        e.bind("<Return>", lambda _e: self.refresh_medicaments())
        ttk.Button(search_bar, text="Rechercher", command=self.refresh_medicaments).pack(side="left")
        ttk.Button(search_bar, text="Tout afficher", command=self._clear_med_search).pack(side="left", padx=6)

        cols = ("id","code","nom","dosage","prix","stock","peremption")
        self.meds_tree = ttk.Treeview(left, columns=cols, show="headings", height=14)
        for c,t,w in [
            ("id","ID",50),("code","Code",110),("nom","Nom",220),("dosage","Dosage",100),
            ("prix","Prix",80),("stock","Stock",70),("peremption","Péremption",110)
        ]:
            self.meds_tree.heading(c, text=t)
            self.meds_tree.column(c, width=w, anchor="center" if c in ("id","prix","stock") else "w")
        self.meds_tree.pack(fill="both", expand=True, padx=8, pady=(0,8))

        add_box = ttk.Frame(left)
        add_box.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Label(add_box, text="Quantité :").pack(side="left")
        self.qty_var = tk.StringVar(value="1")
        ttk.Entry(add_box, textvariable=self.qty_var, width=6).pack(side="left", padx=6)
        ttk.Button(add_box, text="Ajouter à l'ordonnance", command=self.add_to_cart).pack(side="left")

        right = ttk.LabelFrame(main, text="Ordonnance - panier")
        right.pack(side="left", fill="both", expand=True)

        cart_cols = ("med_id","nom","qte","pu","st")
        self.cart_tree = ttk.Treeview(right, columns=cart_cols, show="headings", height=12)
        for c,t,w in [("med_id","ID",50),("nom","Médicament",220),("qte","Qté",50),("pu","PU",70),("st","Sous-total",90)]:
            self.cart_tree.heading(c, text=t)
            self.cart_tree.column(c, width=w, anchor="center" if c in ("med_id","qte") else "w")
        self.cart_tree.pack(fill="both", expand=True, padx=8, pady=8)

        actions = ttk.Frame(right)
        actions.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(actions, text="Modifier quantité", command=self.update_cart_qty).pack(side="left")
        ttk.Button(actions, text="Supprimer ligne", command=self.remove_cart_line).pack(side="left", padx=6)
        ttk.Button(actions, text="Vider", command=self.clear_cart).pack(side="left")

        # ===== Bottom finalize =====
        bottom = ttk.LabelFrame(self, text="Finalisation")
        bottom.pack(fill="x", padx=10, pady=10)

        rowb = ttk.Frame(bottom)
        rowb.pack(fill="x", padx=8, pady=6)

        ttk.Label(rowb, text="Remise (€) :").pack(side="left")
        self.remise_var = tk.StringVar(value="0")
        ttk.Entry(rowb, textvariable=self.remise_var, width=10).pack(side="left", padx=6)

        self.total_var = tk.StringVar(value="Total : 0.00 €")
        ttk.Label(rowb, textvariable=self.total_var).pack(side="left", padx=(20, 0))

        rowc = ttk.Frame(bottom)
        rowc.pack(fill="x", padx=8, pady=6)

        ttk.Button(rowc, text="Valider l'ordonnance", command=self.validate_prescription).pack(side="left")
        ttk.Button(rowc, text="Générer ticket + facture (txt)", command=self.generate_docs).pack(side="left", padx=8)

    def _clear_med_search(self):
        self.med_search_var.set("")
        self.refresh_medicaments()

    def refresh_medicaments(self):
        for it in self.meds_tree.get_children():
            self.meds_tree.delete(it)
        rows = PrescriptionsRepository.search_medicaments(self.med_search_var.get())
        for r in rows:
            self.meds_tree.insert("", "end", values=r)

    def attach_client(self):
        phone = (self.client_phone_var.get() or "").strip()
        if not phone:
            messagebox.showwarning("Attention", "Entrez le téléphone du client.")
            return
        c = PrescriptionsRepository.find_client_by_phone(phone)
        if not c:
            messagebox.showerror("Erreur", "Aucun client trouvé avec ce téléphone.")
            return
        self.client_id = int(c[0])
        self.client_label_var.set(f"Client : {c[2]} {c[1]} ({c[3]})".strip())
        messagebox.showinfo("OK", "Client associé.")

    def refresh_cart(self):
        for it in self.cart_tree.get_children():
            self.cart_tree.delete(it)

        total = 0.0
        for line in self.cart:
            st = float(line["quantite"]) * float(line["prix_unitaire"])
            total += st
            self.cart_tree.insert("", "end", values=(
                line["medicament_id"],
                line["nom"],
                line["quantite"],
                f'{float(line["prix_unitaire"]):.2f}',
                f"{st:.2f}"
            ))
        try:
            remise = float(self.remise_var.get() or 0.0)
        except:
            remise = 0.0
        self.total_var.set(f"Total : {max(0.0, total - remise):.2f} €")

    def add_to_cart(self):
        sel = self.meds_tree.selection()
        if not sel:
            messagebox.showwarning("Attention", "Sélectionnez un médicament.")
            return
        values = self.meds_tree.item(sel[0], "values")
        med_id = int(values[0])
        nom = values[2]
        prix = float(values[4])
        stock = int(values[5])

        try:
            q = int(self.qty_var.get())
        except:
            messagebox.showerror("Erreur", "Quantité invalide.")
            return
        if q <= 0:
            messagebox.showerror("Erreur", "La quantité doit être > 0.")
            return
        if q > stock:
            messagebox.showerror("Erreur", f"Stock insuffisant (disponible : {stock}).")
            return

        for line in self.cart:
            if line["medicament_id"] == med_id:
                new_q = int(line["quantite"]) + q
                if new_q > stock:
                    messagebox.showerror("Erreur", f"Stock insuffisant (disponible : {stock}).")
                    return
                line["quantite"] = new_q
                self.refresh_cart()
                return

        self.cart.append({"medicament_id": med_id, "nom": nom, "quantite": q, "prix_unitaire": prix})
        self.refresh_cart()

    def _get_selected_cart_index(self):
        sel = self.cart_tree.selection()
        if not sel:
            return None
        values = self.cart_tree.item(sel[0], "values")
        med_id = int(values[0])
        for i, line in enumerate(self.cart):
            if line["medicament_id"] == med_id:
                return i
        return None

    def update_cart_qty(self):
        idx = self._get_selected_cart_index()
        if idx is None:
            messagebox.showwarning("Attention", "Sélectionnez une ligne.")
            return

        win = tk.Toplevel(self)
        win.title("Modifier quantité")
        win.resizable(False, False)

        ttk.Label(win, text="Nouvelle quantité :").pack(padx=10, pady=(10, 4))
        var = tk.StringVar(value=str(self.cart[idx]["quantite"]))
        ttk.Entry(win, textvariable=var, width=10).pack(padx=10, pady=4)

        def apply():
            try:
                q = int(var.get())
            except:
                messagebox.showerror("Erreur", "Quantité invalide.")
                return
            if q <= 0:
                messagebox.showerror("Erreur", "Quantité doit être > 0.")
                return
            self.cart[idx]["quantite"] = q
            win.destroy()
            self.refresh_cart()

        ttk.Button(win, text="Valider", command=apply).pack(padx=10, pady=(6, 10))

    def remove_cart_line(self):
        idx = self._get_selected_cart_index()
        if idx is None:
            messagebox.showwarning("Attention", "Sélectionnez une ligne.")
            return
        del self.cart[idx]
        self.refresh_cart()

    def clear_cart(self):
        if not self.cart:
            return
        if not messagebox.askyesno("Confirmation", "Vider l'ordonnance ?"):
            return
        self.cart = []
        self.refresh_cart()

    def validate_prescription(self):
        if not self.client_id:
            messagebox.showerror("Erreur", "Client obligatoire pour une ordonnance.")
            return
        if not self.cart:
            messagebox.showwarning("Attention", "Ordonnance vide.")
            return
        if not messagebox.askyesno("Confirmation", "Valider l'ordonnance ?"):
            return

        info = {
            "numero": self.numero_var.get(),
            "medecin": self.medecin_var.get(),
            "date_ordonnance": self.date_var.get()
        }

        try:
            ord_id, vente_id = PrescriptionsRepository.create_prescription_sale(
                client_id=self.client_id,
                ordonnance_info=info,
                cart_lines=self.cart,
                remise=self.remise_var.get(),
                user_id=None
            )
            self.last_ids = (ord_id, vente_id)
            messagebox.showinfo("Succès", f"Ordonnance enregistrée (ID : {ord_id})\nVente (ID : {vente_id})\nStock mis à jour.")
            # reset UI
            self.cart = []
            self.remise_var.set("0")
            self.numero_var.set("")
            self.medecin_var.set("")
            self.date_var.set("")
            self.refresh_medicaments()
            self.refresh_cart()
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def generate_docs(self):
        if not self.last_ids:
            messagebox.showwarning("Attention", "Aucune ordonnance validée.")
            return
        try:
            ord_id, vente_id = self.last_ids
            ticket_path, facture_path = PrescriptionsRepository.save_docs_to_files(ord_id, vente_id)
            messagebox.showinfo("Documents générés", f"Ticket :\n{ticket_path}\n\nFacture :\n{facture_path}")
        except Exception as e:
            messagebox.showerror("Erreur", str(e))
