import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from services.stock_service import entree_stock, sortie_stock, get_all_stocks
from database.db import get_connection
from ui.medicament_detail_ui import MedicamentDetailUI
from ui.add_medicament_ui import AddMedicamentUI
from ui.edit_medicament_ui import EditMedicamentUI
from utils.window import autosize_and_center


class StockUI(tk.Toplevel):
    def __init__(self, parent, user):
        super().__init__(parent)
        self.user = user
        self.title("Gestion des stocks")
        self.resizable(True, True)

        # ================= FRAME HAUT =================
        top_frame = tk.Frame(self)
        top_frame.pack(fill="x", padx=10, pady=5)

        entree = tk.LabelFrame(top_frame, text="Entrée de stock")
        entree.pack(side="left", expand=True, fill="both", padx=5)

        self.entree_med = self.combo_medicaments(entree)
        self.entree_med.grid(row=0, column=1)

        tk.Label(entree, text="Quantité").grid(row=1, column=0)
        self.entree_qte = tk.Entry(entree)
        self.entree_qte.grid(row=1, column=1)

        tk.Label(entree, text="Prix (€)").grid(row=2, column=0)
        self.entree_prix = tk.Entry(entree)
        self.entree_prix.grid(row=2, column=1)

        tk.Label(entree, text="Péremption").grid(row=3, column=0)
        self.entree_date = tk.Entry(entree)
        self.entree_date.grid(row=3, column=1)

        tk.Button(entree, text="Valider entrée", command=self.handle_entree).grid(
            row=4, columnspan=2, pady=5
        )

        sortie = tk.LabelFrame(top_frame, text="Sortie de stock")
        sortie.pack(side="left", expand=True, fill="both", padx=5)

        self.sortie_med = self.combo_medicaments(sortie)
        self.sortie_med.grid(row=0, column=1)

        tk.Label(sortie, text="Quantité").grid(row=1, column=0)
        self.sortie_qte = tk.Entry(sortie)
        self.sortie_qte.grid(row=1, column=1)

        tk.Button(sortie, text="Valider sortie", command=self.handle_sortie).grid(
            row=2, columnspan=2, pady=5
        )

        if self.user.get("role") == "CONSEILLER":
            self.entree_qte.config(state="disabled")
            self.entree_prix.config(state="disabled")

        # ================= RECHERCHE & FILTRES =================
        action_frame = tk.Frame(self)
        action_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(action_frame, text="Recherche :").pack(side="left")
        self.search_entry = tk.Entry(action_frame, width=30)
        self.search_entry.pack(side="left", padx=5)

        tk.Button(action_frame, text="Rechercher", command=self.search).pack(side="left", padx=5)
        tk.Button(action_frame, text="Tous", command=self.load_all).pack(side="left", padx=5)
        tk.Button(action_frame, text="Stock faible (<5)", command=self.filter_low).pack(side="left", padx=5)
        tk.Button(action_frame, text="Péremption dépassée", command=self.filter_expired).pack(side="left", padx=5)

        tk.Button(action_frame, text="Ajouter", bg="#4CAF50", command=self.open_add).pack(side="right", padx=5)
        tk.Button(action_frame, text="Modifier", command=self.open_edit).pack(side="right", padx=5)

        # ================= TABLE =================
        table_frame = tk.LabelFrame(self, text="Liste des médicaments")
        table_frame.pack(expand=True, fill="both", padx=10, pady=10)

        self.table = ttk.Treeview(
            table_frame,
            columns=("id", "code", "nom", "prix", "stock", "peremption"),
            show="headings",
        )

        for c, t in {
            "id": "ID",
            "code": "Code",
            "nom": "Nom",
            "prix": "Prix (€)",
            "stock": "Stock",
            "peremption": "Péremption",
        }.items():
            self.table.heading(c, text=t)
            self.table.column(c, anchor="center")

        self.table.pack(expand=True, fill="both")
        self.table.bind("<Double-1>", self.open_detail)

        self.data = []
        self.load_all()

        autosize_and_center(self, min_w=1100, min_h=650)

    # ================= LOGIQUE =================

    def combo_medicaments(self, parent):
        cb = ttk.Combobox(parent, state="readonly", width=35)
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, nom_commercial FROM medicaments")
        cb["values"] = [f"{i} - {n}" for i, n in cur.fetchall()]
        conn.close()
        return cb

    def load_all(self):
        self.data = get_all_stocks()
        self.refresh(self.data)

    def search(self):
        key = self.search_entry.get().lower()
        self.refresh([m for m in self.data if key in m[1].lower() or key in m[2].lower()])

    def filter_low(self):
        self.refresh([m for m in self.data if m[4] <= 5])

    def filter_expired(self):
        today = datetime.today().date()
        self.refresh([m for m in self.data if m[5] and datetime.strptime(m[5], "%Y-%m-%d").date() < today])

    def refresh(self, rows):
        self.table.delete(*self.table.get_children())
        for r in rows:
            self.table.insert("", "end", values=r)

    def open_detail(self, event):
        sel = self.table.focus()
        if sel:
            MedicamentDetailUI(self, self.table.item(sel)["values"][0])

    def open_add(self):
        AddMedicamentUI(self, self.load_all)

    def open_edit(self):
        sel = self.table.focus()
        if not sel:
            messagebox.showwarning("Attention", "Sélectionnez un médicament")
            return
        med_id = self.table.item(sel)["values"][0]
        EditMedicamentUI(self, med_id, self.load_all)

    def handle_entree(self):
        try:
            med_id = int(self.entree_med.get().split(" - ")[0])
            entree_stock(med_id, int(self.entree_qte.get()), float(self.entree_prix.get()), self.entree_date.get())
            self.load_all()
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def handle_sortie(self):
        try:
            med_id = int(self.sortie_med.get().split(" - ")[0])
            sortie_stock(med_id, int(self.sortie_qte.get()))
            self.load_all()
        except Exception as e:
            messagebox.showerror("Erreur", str(e))
