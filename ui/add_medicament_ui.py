import tkinter as tk
from tkinter import messagebox
from services.medicament_service import add_medicament

class AddMedicamentUI(tk.Toplevel):
    def __init__(self, parent, refresh_callback):
        super().__init__(parent)
        self.refresh_callback = refresh_callback
        self.title("Ajouter un médicament")
        self.geometry("400x380")
        self.resizable(False, False)

        self.entries = {}

        fields = [
            ("Code", "code"),
            ("Nom", "nom"),
            ("Catégorie", "categorie"),
            ("Prix (€)", "prix"),
            ("Stock initial", "stock"),
            ("Date péremption (YYYY-MM-DD)", "peremption")
        ]

        for i, (label, key) in enumerate(fields):
            tk.Label(self, text=label).grid(row=i, column=0, padx=10, pady=5, sticky="w")
            e = tk.Entry(self, width=30)
            e.grid(row=i, column=1, padx=10, pady=5)
            self.entries[key] = e

        tk.Button(
            self,
            text="Ajouter",
            bg="#4CAF50",
            fg="black",
            command=self.save
        ).grid(row=len(fields), columnspan=2, pady=20)

    def save(self):
        try:
            data = {k: v.get() for k, v in self.entries.items()}
            data["prix"] = float(data["prix"])
            data["stock"] = int(data["stock"])

            add_medicament(data)
            self.refresh_callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Erreur", str(e))
