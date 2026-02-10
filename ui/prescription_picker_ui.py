import tkinter as tk
from tkinter import ttk, messagebox

from modules.prescriptions_repository import PrescriptionsRepository
from utils.window import autosize_and_center


class PrescriptionPickerUI(tk.Toplevel):
    """
    Fenêtre de sélection de médicaments "ordonnance".
    - Ne valide aucune vente.
    - Ajoute directement au panier principal via on_add_lines(lines, ordonnance_info).

    lines: list[dict] avec:
      {
        "medicament_id": int,
        "nom": str,
        "code": str,
        "quantite": int,
        "prix_unitaire": float,   # ici 0.0 pour ordonnance
        "ordonnance": True
      }

    ordonnance_info:
      {"numero": str, "medecin": str, "date_ordonnance": str}
    """

    def __init__(self, parent, on_add_lines):
        super().__init__(parent)
        self.on_add_lines = on_add_lines

        self.title("Ordonnance - Ajouter au panier")
        self.resizable(True, True)

        self.numero_var = tk.StringVar(master=self)
        self.medecin_var = tk.StringVar(master=self)
        self.date_var = tk.StringVar(master=self)

        self.med_search_var = tk.StringVar(master=self, value="")
        self.qty_var = tk.StringVar(master=self, value="1")

        self._build_ui()
        self.refresh_medicaments()

        autosize_and_center(self, min_w=1100, min_h=650)

    def _build_ui(self):
        top = ttk.LabelFrame(self, text="Informations ordonnance (optionnel)")
        top.pack(fill="x", padx=10, pady=10)

        row1 = ttk.Frame(top)
        row1.pack(fill="x", padx=8, pady=6)

        ttk.Label(row1, text="Numéro :").pack(side="left")
        ttk.Entry(row1, textvariable=self.numero_var, width=18).pack(side="left", padx=6)

        ttk.Label(row1, text="Médecin :").pack(side="left", padx=(15, 0))
        ttk.Entry(row1, textvariable=self.medecin_var, width=24).pack(side="left", padx=6)

        ttk.Label(row1, text="Date (YYYY-MM-DD) :").pack(side="left", padx=(15, 0))
        ttk.Entry(row1, textvariable=self.date_var, width=14).pack(side="left", padx=6)

        main = ttk.Frame(self)
        main.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        left = ttk.LabelFrame(main, text="Médicaments")
        left.pack(side="left", fill="both", expand=True)

        search_bar = ttk.Frame(left)
        search_bar.pack(fill="x", padx=8, pady=8)

        ttk.Label(search_bar, text="Recherche :").pack(side="left")
        e = ttk.Entry(search_bar, textvariable=self.med_search_var, width=35)
        e.pack(side="left", padx=8)
        e.bind("<Return>", lambda _e: self.refresh_medicaments())
        ttk.Button(search_bar, text="Rechercher", command=self.refresh_medicaments).pack(side="left")
        ttk.Button(search_bar, text="Tout afficher", command=self._clear_search).pack(side="left", padx=6)

        cols = ("id", "code", "nom", "dosage", "prix", "stock", "peremption")
        self.meds_tree = ttk.Treeview(left, columns=cols, show="headings", height=16)
        for c, t, w in [
            ("id", "ID", 60),
            ("code", "Code", 110),
            ("nom", "Nom", 240),
            ("dosage", "Dosage", 100),
            ("prix", "Prix", 80),
            ("stock", "Stock", 70),
            ("peremption", "Péremption", 110),
        ]:
            self.meds_tree.heading(c, text=t)
            self.meds_tree.column(c, width=w, anchor="center" if c in ("id", "prix", "stock") else "w")
        self.meds_tree.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        add_box = ttk.Frame(left)
        add_box.pack(fill="x", padx=8, pady=(0, 10))

        ttk.Label(add_box, text="Quantité :").pack(side="left")
        ttk.Entry(add_box, textvariable=self.qty_var, width=6).pack(side="left", padx=6)
        ttk.Button(add_box, text="Ajouter au panier (Ordonnance)", command=self.add_selected_to_main).pack(side="left")

        bottom = ttk.Frame(self)
        bottom.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(bottom, text="Fermer", command=self.destroy).pack(side="right")

    def _clear_search(self):
        self.med_search_var.set("")
        self.refresh_medicaments()

    def refresh_medicaments(self):
        for it in self.meds_tree.get_children():
            self.meds_tree.delete(it)

        rows = PrescriptionsRepository.search_medicaments(self.med_search_var.get())
        for r in rows:
            self.meds_tree.insert("", "end", values=r)

    def add_selected_to_main(self):
        sel = self.meds_tree.selection()
        if not sel:
            messagebox.showwarning("Attention", "Sélectionnez un médicament.")
            return

        values = self.meds_tree.item(sel[0], "values")
        med_id = int(values[0])
        code = values[1]
        nom = values[2]
        stock = int(values[5])

        try:
            q = int(self.qty_var.get())
        except Exception:
            messagebox.showerror("Erreur", "Quantité invalide.")
            return

        if q <= 0:
            messagebox.showerror("Erreur", "La quantité doit être > 0.")
            return
        if q > stock:
            messagebox.showerror("Erreur", f"Stock insuffisant (disponible : {stock}).")
            return

        ordonnance_info = {
            "numero": self.numero_var.get(),
            "medecin": self.medecin_var.get(),
            "date_ordonnance": self.date_var.get(),
        }

        line = {
            "medicament_id": med_id,
            "code": code,
            "nom": nom,
            "quantite": q,
            "prix_unitaire": 0.0,
            "ordonnance": True,
        }

        self.on_add_lines([line], ordonnance_info)
        messagebox.showinfo("OK", "Ajouté au panier principal (Ordonnance).")
