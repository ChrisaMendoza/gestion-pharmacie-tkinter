import tkinter as tk

from services.medicament_service import get_medicament_details_by_id
from utils.window import autosize_and_center


class MedicamentDetailUI(tk.Toplevel):
    def __init__(self, parent, med_id):
        super().__init__(parent)
        self.title("Fiche médicament")
        self.resizable(False, False)

        med = get_medicament_details_by_id(med_id)
        if not med:
            tk.Label(self, text="Médicament introuvable").pack(padx=12, pady=12)
            autosize_and_center(self, min_w=300, min_h=120)
            return

        labels = [
            ("Code", med[0]),
            ("Nom", med[1]),
            ("Catégorie", med[2]),
            ("Prix (€)", med[3]),
            ("Stock", med[4]),
            ("Seuil alerte", med[5]),
            ("Péremption", med[6]),
        ]

        for l, v in labels:
            f = tk.Frame(self)
            f.pack(fill="x", padx=10, pady=6)
            tk.Label(f, text=l, width=15, anchor="w", font=("Arial", 10, "bold")).pack(side="left")
            tk.Label(f, text=v).pack(side="left")

        autosize_and_center(self, min_w=420, min_h=260)
