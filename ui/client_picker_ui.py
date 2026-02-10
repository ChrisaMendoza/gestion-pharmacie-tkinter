import tkinter as tk
from tkinter import ttk, messagebox

from modules.clients_repository import ClientsRepository
from utils.window import autosize_and_center


class ClientPickerUI(tk.Toplevel):
    def __init__(self, parent, on_select):
        super().__init__(parent)
        self.on_select = on_select

        self.title("Associer / Créer un client")
        self.resizable(True, True)

        self.search_var = tk.StringVar(master=self)

        self.nom_var = tk.StringVar(master=self)
        self.prenom_var = tk.StringVar(master=self)
        self.tel_var = tk.StringVar(master=self)
        self.dn_var = tk.StringVar(master=self)
        self.secu_var = tk.StringVar(master=self)

        self._build_ui()
        self.refresh()

        autosize_and_center(self, min_w=900, min_h=520)

    def _build_ui(self):
        root = ttk.Frame(self)
        root.pack(fill="both", expand=True, padx=10, pady=10)

        top = ttk.Frame(root)
        top.pack(fill="x")

        ttk.Label(top, text="Recherche :").pack(side="left")
        e = ttk.Entry(top, textvariable=self.search_var, width=45)
        e.pack(side="left", padx=8)
        e.bind("<Return>", lambda _e: self.refresh())

        ttk.Button(top, text="Rechercher", command=self.refresh).pack(side="left")
        ttk.Button(top, text="Tout", command=self._clear_search).pack(side="left", padx=6)

        main = ttk.Frame(root)
        main.pack(fill="both", expand=True, pady=(10, 0))

        form = ttk.LabelFrame(main, text="Créer un nouveau client")
        form.pack(side="left", fill="y", padx=(0, 10))

        self._field(form, "Nom", self.nom_var, 0)
        self._field(form, "Prénom", self.prenom_var, 1)
        self._field(form, "Téléphone (obligatoire)", self.tel_var, 2)
        self._field(form, "Date naissance (YYYY-MM-DD)", self.dn_var, 3)
        self._field(form, "Sécu (13/15 chiffres)", self.secu_var, 4)

        btns = ttk.Frame(form)
        btns.grid(row=5, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        ttk.Button(btns, text="Créer et sélectionner", command=self.create_and_select).pack(fill="x", pady=2)
        ttk.Button(btns, text="Vider", command=self.clear_form).pack(fill="x", pady=2)

        table_box = ttk.LabelFrame(main, text="Clients")
        table_box.pack(side="left", fill="both", expand=True)

        cols = ("id", "nom", "prenom", "telephone", "dn", "secu")
        self.tree = ttk.Treeview(table_box, columns=cols, show="headings", height=16)

        for c, t, w in [
            ("id", "ID", 55),
            ("nom", "Nom", 140),
            ("prenom", "Prénom", 140),
            ("telephone", "Téléphone", 120),
            ("dn", "Naissance", 120),
            ("secu", "Sécu", 170),
        ]:
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor="center" if c == "id" else "w")

        self.tree.pack(fill="both", expand=True, padx=8, pady=8)
        self.tree.bind("<Double-1>", lambda _e: self.select_current())

        bottom = ttk.Frame(root)
        bottom.pack(fill="x", pady=(10, 0))

        ttk.Button(bottom, text="Sélectionner", command=self.select_current).pack(side="left")
        ttk.Button(bottom, text="Fermer", command=self.destroy).pack(side="right")

    def _field(self, parent, label, var, row):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=10, pady=6)
        ttk.Entry(parent, textvariable=var, width=30).grid(row=row, column=1, sticky="ew", padx=10, pady=6)
        parent.grid_columnconfigure(1, weight=1)

    def _clear_search(self):
        self.search_var.set("")
        self.refresh()

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        rows = ClientsRepository.search_clients(self.search_var.get())
        for r in rows:
            self.tree.insert("", "end", values=(r[0], r[1], r[2], r[3], r[6], r[7]))

    def clear_form(self):
        self.nom_var.set("")
        self.prenom_var.set("")
        self.tel_var.set("")
        self.dn_var.set("")
        self.secu_var.set("")

    def select_current(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Attention", "Sélectionne un client dans la liste.")
            return

        v = self.tree.item(sel[0], "values")
        client = {
            "id": int(v[0]),
            "nom": v[1],
            "prenom": v[2],
            "telephone": v[3],
            "date_naissance": v[4],
            "secu": v[5],
        }
        self.on_select(client)
        self.destroy()

    def create_and_select(self):
        try:
            client_id = ClientsRepository.add_client(
                nom=self.nom_var.get(),
                prenom=self.prenom_var.get(),
                telephone=self.tel_var.get(),
                email="",
                carte_fidelite="",
                date_naissance=self.dn_var.get(),
                secu=self.secu_var.get(),
            )
            messagebox.showinfo("Succès", f"Client créé (ID : {client_id}).")
            self.refresh()

            for item in self.tree.get_children():
                v = self.tree.item(item, "values")
                if v and int(v[0]) == int(client_id):
                    self.tree.selection_set(item)
                    self.tree.focus(item)
                    self.tree.see(item)
                    break

            self.select_current()
        except Exception as e:
            messagebox.showerror("Erreur", str(e))
