import tkinter as tk
from tkinter import messagebox

from services.medicament_service import add_medicament, update_medicament
from utils.window import autosize_and_center


class MedicamentFormUI(tk.Toplevel):
    def __init__(self, parent, refresh_callback, medicament=None):
        super().__init__(parent)
        self.refresh_callback = refresh_callback
        self.medicament = medicament
        self.title("Ajouter un médicament" if medicament is None else "Modifier un médicament")
        self.resizable(False, False)

        self.entries = {}
        fields = ["code", "nom_commercial", "categorie", "prix_vente", "date_peremption"]

        for i, field in enumerate(fields):
            tk.Label(self, text=field).grid(row=i, column=0, padx=10, pady=5, sticky="w")
            e = tk.Entry(self, width=30)
            e.grid(row=i, column=1, padx=10, pady=5)
            self.entries[field] = e

        if medicament:
            for key, value in medicament.items():
                self.entries[key].insert(0, value)
            self.entries["code"].config(state="disabled")

        tk.Button(self, text="Enregistrer", width=20, command=self.save).grid(
            row=len(fields), columnspan=2, pady=20
        )

        autosize_and_center(self, min_w=420, min_h=260)

    def save(self):
        data = {k: v.get() for k, v in self.entries.items()}

        try:
            if self.medicament is None:
                add_medicament(data)
            else:
                update_medicament(self.medicament["code"], data)

            self.refresh_callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Erreur", str(e))
