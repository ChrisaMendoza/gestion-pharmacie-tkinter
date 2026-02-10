import tkinter as tk
from tkinter import ttk, messagebox

from modules.clients_repository import ClientsRepository


class ClientsFrame(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.selected_client_id = None

        self._build_ui()
        self.refresh_clients()

    def _build_ui(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=10)

        ttk.Label(top, text="Recherche :").pack(side="left")
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(top, textvariable=self.search_var, width=35)
        search_entry.pack(side="left", padx=8)
        search_entry.bind("<Return>", lambda e: self.refresh_clients())

        ttk.Button(top, text="Rechercher", command=self.refresh_clients).pack(side="left")
        ttk.Button(top, text="Afficher tout", command=self._clear_search).pack(side="left", padx=6)

        main = ttk.Frame(self)
        main.pack(fill="both", expand=True, padx=10, pady=5)

        form = ttk.LabelFrame(main, text="Fiche client")
        form.pack(side="left", fill="y", padx=(0, 10))

        self.nom_var = tk.StringVar()
        self.prenom_var = tk.StringVar()
        self.dn_var = tk.StringVar()
        self.secu_var = tk.StringVar()
        self.tel_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.fid_var = tk.StringVar()

        self._field(form, "Nom", self.nom_var, 0)
        self._field(form, "Prénom", self.prenom_var, 1)
        self._field(form, "Date naissance (YYYY-MM-DD)", self.dn_var, 2)
        self._field(form, "Sécu (13 ou 15 chiffres)", self.secu_var, 3)
        self._field(form, "Téléphone", self.tel_var, 4)
        self._field(form, "Email", self.email_var, 5)
        self._field(form, "Carte fidélité", self.fid_var, 6)

        btns = ttk.Frame(form)
        btns.grid(row=7, column=0, columnspan=2, pady=10, padx=10, sticky="ew")

        ttk.Button(btns, text="Ajouter", command=self.on_add).pack(fill="x", pady=2)
        ttk.Button(btns, text="Modifier", command=self.on_update).pack(fill="x", pady=2)
        ttk.Button(btns, text="Supprimer", command=self.on_delete).pack(fill="x", pady=2)
        ttk.Button(btns, text="Vider", command=self.clear_form).pack(fill="x", pady=2)

        table_frame = ttk.Frame(main)
        table_frame.pack(side="left", fill="both", expand=True)

        # Ordre d'affichage (Treeview)
        cols = ("id", "nom", "prenom", "date_naissance", "secu", "telephone", "email", "fid")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=14)
        for c, t in [
            ("id", "ID"),
            ("nom", "Nom"),
            ("prenom", "Prénom"),
            ("date_naissance", "Naissance"),
            ("secu", "Sécu"),
            ("telephone", "Téléphone"),
            ("email", "Email"),
            ("fid", "Fidélité"),
        ]:
            self.tree.heading(c, text=t)

        self.tree.column("id", width=50, anchor="center")
        self.tree.column("nom", width=120)
        self.tree.column("prenom", width=120)
        self.tree.column("date_naissance", width=110)
        self.tree.column("secu", width=140)
        self.tree.column("telephone", width=110)
        self.tree.column("email", width=170)
        self.tree.column("fid", width=110)

        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        hist = ttk.LabelFrame(self, text="Historique du client sélectionné")
        hist.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Label(hist, text="Ventes").pack(anchor="w", padx=8, pady=(6, 0))
        self.sales_tree = ttk.Treeview(
            hist, columns=("id", "type", "total", "remise", "date"), show="headings", height=6
        )
        for c, t, w in [
            ("id", "ID", 60),
            ("type", "Type", 110),
            ("total", "Total", 100),
            ("remise", "Remise", 100),
            ("date", "Date", 180),
        ]:
            self.sales_tree.heading(c, text=t)
            self.sales_tree.column(c, width=w, anchor="center" if c in ("id", "type") else "w")
        self.sales_tree.pack(fill="x", padx=8, pady=6)

        ttk.Label(hist, text="Ordonnances").pack(anchor="w", padx=8, pady=(6, 0))
        self.rx_tree = ttk.Treeview(
            hist, columns=("id", "numero", "medecin", "date_o", "date_s"), show="headings", height=6
        )
        for c, t, w in [
            ("id", "ID", 60),
            ("numero", "Numéro", 120),
            ("medecin", "Médecin", 180),
            ("date_o", "Date ordonnance", 140),
            ("date_s", "Date saisie", 180),
        ]:
            self.rx_tree.heading(c, text=t)
            self.rx_tree.column(c, width=w, anchor="center" if c == "id" else "w")
        self.rx_tree.pack(fill="x", padx=8, pady=6)

    def _field(self, parent, label, var, row):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=10, pady=6)
        ttk.Entry(parent, textvariable=var, width=30).grid(row=row, column=1, sticky="ew", padx=10, pady=6)
        parent.grid_columnconfigure(1, weight=1)

    def _clear_search(self):
        self.search_var.set("")
        self.refresh_clients()

    def refresh_clients(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        rows = ClientsRepository.search_clients(self.search_var.get())
        for r in rows:
            # r = (id, nom, prenom, telephone, email, fid, date_naissance, secu)
            self.tree.insert(
                "",
                "end",
                values=(r[0], r[1], r[2], r[6], r[7], r[3], r[4], r[5]),
            )

    def clear_form(self):
        self.selected_client_id = None
        self.nom_var.set("")
        self.prenom_var.set("")
        self.dn_var.set("")
        self.secu_var.set("")
        self.tel_var.set("")
        self.email_var.set("")
        self.fid_var.set("")
        self._clear_history_tables()

    def _clear_history_tables(self):
        for t in (self.sales_tree, self.rx_tree):
            for item in t.get_children():
                t.delete(item)

    def on_select(self, _event=None):
        sel = self.tree.selection()
        if not sel:
            return

        values = self.tree.item(sel[0], "values")
        # values suit l'ordre du Treeview:
        # (id, nom, prenom, date_naissance, secu, telephone, email, fid)
        self.selected_client_id = int(values[0])

        self.nom_var.set(values[1])
        self.prenom_var.set(values[2])
        self.dn_var.set(values[3])
        self.secu_var.set(values[4])
        self.tel_var.set(values[5])
        self.email_var.set(values[6])
        self.fid_var.set(values[7])

        self.refresh_history()

    def refresh_history(self):
        self._clear_history_tables()
        if not self.selected_client_id:
            return

        data = ClientsRepository.get_client_history(self.selected_client_id)

        for v in data["ventes"]:
            self.sales_tree.insert("", "end", values=v)

        for o in data["ordonnances"]:
            self.rx_tree.insert("", "end", values=o)

    def on_add(self):
        try:
            client_id = ClientsRepository.add_client(
                nom=self.nom_var.get(),
                prenom=self.prenom_var.get(),
                telephone=self.tel_var.get(),
                email=self.email_var.get(),
                carte_fidelite=self.fid_var.get(),
                date_naissance=self.dn_var.get(),
                secu=self.secu_var.get(),
            )
            messagebox.showinfo("Succès", f"Client ajouté (ID : {client_id}).")
            self.refresh_clients()
            self.clear_form()
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def on_update(self):
        if not self.selected_client_id:
            messagebox.showwarning("Attention", "Veuillez sélectionner un client à modifier.")
            return
        if not messagebox.askyesno("Confirmation", "Confirmer la modification de ce client ?"):
            return
        try:
            ClientsRepository.update_client(
                client_id=self.selected_client_id,
                nom=self.nom_var.get(),
                prenom=self.prenom_var.get(),
                telephone=self.tel_var.get(),
                email=self.email_var.get(),
                carte_fidelite=self.fid_var.get(),
                date_naissance=self.dn_var.get(),
                secu=self.secu_var.get(),
            )
            messagebox.showinfo("Succès", "Client modifié.")
            self.refresh_clients()
            self.refresh_history()
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def on_delete(self):
        if not self.selected_client_id:
            messagebox.showwarning("Attention", "Veuillez sélectionner un client à supprimer.")
            return
        if not messagebox.askyesno("Confirmation", "Supprimer ce client ? (action irréversible)"):
            return
        try:
            ClientsRepository.delete_client(self.selected_client_id)
            messagebox.showinfo("Succès", "Client supprimé.")
            self.refresh_clients()
            self.clear_form()
        except Exception as e:
            messagebox.showerror("Erreur", str(e))
