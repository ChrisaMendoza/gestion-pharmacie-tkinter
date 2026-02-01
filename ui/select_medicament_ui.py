import tkinter as tk
from tkinter import ttk, messagebox
from services.stock_service import get_medicaments_for_sale
from ui.medicament_detail_ui import MedicamentDetailUI

class SelectMedicamentUI(tk.Toplevel):
    def __init__(self, parent, add_callback):
        super().__init__(parent)
        self.title("Ajouter un médicament à la vente")
        self.geometry("850x500")

        self.add_callback = add_callback

        # ===== RECHERCHE =====
        search_frame = tk.Frame(self)
        search_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(search_frame, text="Recherche :").pack(side="left")
        self.search_entry = tk.Entry(search_frame, width=40)
        self.search_entry.pack(side="left", padx=5)

        tk.Button(search_frame, text="Rechercher", command=self.search).pack(side="left")
        tk.Button(search_frame, text="Tout afficher", command=self.load).pack(side="left")

        # ===== TABLE =====
        self.table = ttk.Treeview(
            self,
            columns=("id", "code", "nom", "prix", "stock"),
            show="headings"
        )

        for c, t in {
            "id": "ID",
            "code": "Code",
            "nom": "Nom",
            "prix": "Prix (€)",
            "stock": "Stock"
        }.items():
            self.table.heading(c, text=t)
            self.table.column(c, anchor="center")

        self.table.pack(expand=True, fill="both", padx=10, pady=10)
        self.table.bind("<Double-1>", self.open_detail)

        # ===== ACTION =====
        tk.Button(
            self,
            text="Ajouter au panier",
            bg="#4CAF50",
            fg="white",
            command=self.add_to_cart
        ).pack(pady=10)

        self.medicaments = []
        self.load()

    def load(self):
        self.medicaments = get_medicaments_for_sale()
        self.refresh(self.medicaments)

    def refresh(self, data):
        self.table.delete(*self.table.get_children())
        for med in data:
            self.table.insert("", "end", values=med)

    def search(self):
        key = self.search_entry.get().lower()
        filtered = [m for m in self.medicaments if key in m[2].lower() or key in m[1].lower()]
        self.refresh(filtered)

    def open_detail(self, event):
        sel = self.table.focus()
        if not sel:
            return
        med_id = self.table.item(sel)["values"][0]
        MedicamentDetailUI(self, med_id)

    def add_to_cart(self):
        sel = self.table.focus()
        if not sel:
            messagebox.showwarning("Attention", "Sélectionnez un médicament")
            return
        self.add_callback(self.table.item(sel)["values"])
        self.destroy()
