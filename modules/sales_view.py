import tkinter as tk
from tkinter import ttk, messagebox

from modules.sales_repository import SalesRepository

class SalesFrame(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.cart = []  # list of dict lines
        self.client_id = None
        self.client_label_var = tk.StringVar(value="Client : (aucun)")

        self._build_ui()
        self.refresh_medicaments()
        self.refresh_cart()

    def _build_ui(self):
        # ====== TOP SEARCH ======
        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=10)

        ttk.Label(top, text="Recherche médicament :").pack(side="left")
        self.med_search_var = tk.StringVar()
        e = ttk.Entry(top, textvariable=self.med_search_var, width=40)
        e.pack(side="left", padx=8)
        e.bind("<Return>", lambda _e: self.refresh_medicaments())

        ttk.Button(top, text="Rechercher", command=self.refresh_medicaments).pack(side="left")
        ttk.Button(top, text="Tout afficher", command=self._clear_med_search).pack(side="left", padx=6)

        # ====== MAIN: meds + cart ======
        main = ttk.Frame(self)
        main.pack(fill="both", expand=True, padx=10, pady=5)

        # --- left: medicaments list
        left = ttk.LabelFrame(main, text="Médicaments")
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        cols = ("id","code","nom","dosage","prix","stock","peremption")
        self.meds_tree = ttk.Treeview(left, columns=cols, show="headings", height=16)
        for c,t,w in [
            ("id","ID",50),("code","Code",110),("nom","Nom",220),("dosage","Dosage",100),
            ("prix","Prix",80),("stock","Stock",70),("peremption","Péremption",110)
        ]:
            self.meds_tree.heading(c, text=t)
            self.meds_tree.column(c, width=w, anchor="center" if c in ("id","prix","stock") else "w")
        self.meds_tree.pack(fill="both", expand=True, padx=8, pady=8)

        add_box = ttk.Frame(left)
        add_box.pack(fill="x", padx=8, pady=(0, 8))

        ttk.Label(add_box, text="Quantité :").pack(side="left")
        self.qty_var = tk.StringVar(value="1")
        ttk.Entry(add_box, textvariable=self.qty_var, width=6).pack(side="left", padx=6)
        ttk.Button(add_box, text="Ajouter au panier", command=self.add_to_cart).pack(side="left")

        # --- right: cart
        right = ttk.LabelFrame(main, text="Panier")
        right.pack(side="left", fill="both", expand=True)

        cart_cols = ("med_id","nom","qte","pu","st")
        self.cart_tree = ttk.Treeview(right, columns=cart_cols, show="headings", height=12)
        for c,t,w in [("med_id","ID",50),("nom","Médicament",220),("qte","Qté",50),("pu","PU",70),("st","Sous-total",90)]:
            self.cart_tree.heading(c, text=t)
            self.cart_tree.column(c, width=w, anchor="center" if c in ("med_id","qte") else "w")
        self.cart_tree.pack(fill="both", expand=True, padx=8, pady=8)

        cart_actions = ttk.Frame(right)
        cart_actions.pack(fill="x", padx=8, pady=(0, 8))

        ttk.Button(cart_actions, text="Modifier quantité", command=self.update_cart_qty).pack(side="left")
        ttk.Button(cart_actions, text="Supprimer ligne", command=self.remove_cart_line).pack(side="left", padx=6)
        ttk.Button(cart_actions, text="Vider panier", command=self.clear_cart).pack(side="left")

        # ====== BOTTOM: client + total + validate ======
        bottom = ttk.LabelFrame(self, text="Finalisation")
        bottom.pack(fill="x", padx=10, pady=10)

        # client association
        client_row = ttk.Frame(bottom)
        client_row.pack(fill="x", padx=8, pady=6)

        ttk.Label(client_row, textvariable=self.client_label_var).pack(side="left")

        ttk.Label(client_row, text="Téléphone client (optionnel) :").pack(side="left", padx=(20, 6))
        self.client_phone_var = tk.StringVar()
        ttk.Entry(client_row, textvariable=self.client_phone_var, width=18).pack(side="left")
        ttk.Button(client_row, text="Associer", command=self.attach_client).pack(side="left", padx=6)
        ttk.Button(client_row, text="Désassocier", command=self.detach_client).pack(side="left")

        # total/remise
        total_row = ttk.Frame(bottom)
        total_row.pack(fill="x", padx=8, pady=6)

        ttk.Label(total_row, text="Remise (€) :").pack(side="left")
        self.remise_var = tk.StringVar(value="0")
        ttk.Entry(total_row, textvariable=self.remise_var, width=10).pack(side="left", padx=6)

        self.total_var = tk.StringVar(value="Total : 0.00 €")
        ttk.Label(total_row, textvariable=self.total_var).pack(side="left", padx=(20, 0))

        # validate
        validate_row = ttk.Frame(bottom)
        validate_row.pack(fill="x", padx=8, pady=6)

        ttk.Button(validate_row, text="Valider la vente", command=self.validate_sale).pack(side="left")
        ttk.Button(validate_row, text="Imprimer ticket (txt)", command=self.print_last_ticket).pack(side="left", padx=8)

        self.last_sale_id = None

    def _clear_med_search(self):
        self.med_search_var.set("")
        self.refresh_medicaments()

    def refresh_medicaments(self):
        for it in self.meds_tree.get_children():
            self.meds_tree.delete(it)
        rows = SalesRepository.search_medicaments(self.med_search_var.get())
        for r in rows:
            self.meds_tree.insert("", "end", values=r)

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
        # apply remise for display
        try:
            remise = float(self.remise_var.get() or 0.0)
        except:
            remise = 0.0
        total_net = max(0.0, total - remise)
        self.total_var.set(f"Total : {total_net:.2f} €")

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

        # si déjà dans panier → additionner
        for line in self.cart:
            if line["medicament_id"] == med_id:
                new_q = int(line["quantite"]) + q
                if new_q > stock:
                    messagebox.showerror("Erreur", f"Stock insuffisant (disponible : {stock}).")
                    return
                line["quantite"] = new_q
                self.refresh_cart()
                return

        self.cart.append({
            "medicament_id": med_id,
            "nom": nom,
            "quantite": q,
            "prix_unitaire": prix
        })
        self.refresh_cart()

    def _get_selected_cart_line_index(self):
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
        idx = self._get_selected_cart_line_index()
        if idx is None:
            messagebox.showwarning("Attention", "Sélectionnez une ligne du panier.")
            return

        # popup simple
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
                messagebox.showerror("Erreur", "La quantité doit être > 0.")
                return
            self.cart[idx]["quantite"] = q
            win.destroy()
            self.refresh_cart()

        ttk.Button(win, text="Valider", command=apply).pack(padx=10, pady=(6, 10))

    def remove_cart_line(self):
        idx = self._get_selected_cart_line_index()
        if idx is None:
            messagebox.showwarning("Attention", "Sélectionnez une ligne du panier.")
            return
        del self.cart[idx]
        self.refresh_cart()

    def clear_cart(self):
        if not self.cart:
            return
        if not messagebox.askyesno("Confirmation", "Vider le panier ?"):
            return
        self.cart = []
        self.refresh_cart()

    def attach_client(self):
        phone = (self.client_phone_var.get() or "").strip()
        if not phone:
            messagebox.showwarning("Attention", "Entrez un téléphone client.")
            return
        c = SalesRepository.find_client_by_phone(phone)
        if not c:
            messagebox.showerror("Erreur", "Aucun client trouvé avec ce téléphone.")
            return
        self.client_id = int(c[0])
        self.client_label_var.set(f"Client : {c[2]} {c[1]} ({c[3]})".strip())
        messagebox.showinfo("OK", "Client associé à la vente.")

    def detach_client(self):
        self.client_id = None
        self.client_label_var.set("Client : (aucun)")
        self.client_phone_var.set("")

    def validate_sale(self):
        if not self.cart:
            messagebox.showwarning("Attention", "Panier vide.")
            return

        if not messagebox.askyesno("Confirmation", "Valider la vente ?"):
            return

        try:
            vente_id = SalesRepository.create_sale(
                cart_lines=self.cart,
                remise=self.remise_var.get(),
                client_id=self.client_id,
                user_id=None
            )
            self.last_sale_id = vente_id
            messagebox.showinfo("Succès", f"Vente enregistrée (ID : {vente_id}).\nStock mis à jour.")
            # reset
            self.cart = []
            self.remise_var.set("0")
            self.detach_client()
            self.refresh_medicaments()
            self.refresh_cart()
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def print_last_ticket(self):
        if not self.last_sale_id:
            messagebox.showwarning("Attention", "Aucune vente validée à imprimer.")
            return
        try:
            path = SalesRepository.save_ticket_to_file(self.last_sale_id)
            messagebox.showinfo("Ticket généré", f"Ticket enregistré :\n{path}")
        except Exception as e:
            messagebox.showerror("Erreur", str(e))
