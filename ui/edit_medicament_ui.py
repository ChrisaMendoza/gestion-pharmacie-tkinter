import tkinter as tk
from tkinter import messagebox

from services.medicament_service import get_medicament_by_id, update_medicament
from utils.window import autosize_and_center


class EditMedicamentUI(tk.Toplevel):
    def __init__(self, parent, med_id, refresh_callback):
        super().__init__(parent)
        self.med_id = med_id
        self.refresh_callback = refresh_callback

        self.title("Modifier un médicament")
        self.resizable(False, False)

        med = get_medicament_by_id(med_id)
        if not med:
            messagebox.showerror("Erreur", "Médicament introuvable")
            self.destroy()
            return

        self.entries = {}

        fields = [
            ("Code", "code", med[1]),
            ("Nom", "nom", med[2]),
            ("Catégorie", "categorie", med[3]),
            ("Prix (€)", "prix", med[4]),
            ("Stock", "stock", med[5]),
            ("Péremption (YYYY-MM-DD)", "peremption", med[6]),
        ]

        for i, (label, key, value) in enumerate(fields):
            tk.Label(self, text=label).grid(row=i, column=0, padx=10, pady=5, sticky="w")
            e = tk.Entry(self, width=30)
            e.insert(0, value)
            e.grid(row=i, column=1, padx=10, pady=5)
            self.entries[key] = e

        tk.Button(
            self,
            text="Enregistrer",
            bg="#2196F3",
            fg="white",
            command=self.save,
        ).grid(row=len(fields), columnspan=2, pady=20)

        autosize_and_center(self, min_w=420, min_h=320)

    def save(self):
        try:
            data = {k: v.get() for k, v in self.entries.items()}
            data["prix"] = float(data["prix"])
            data["stock"] = int(data["stock"])

            update_medicament(self.med_id, data)
            self.refresh_callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Erreur", str(e))
