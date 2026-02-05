import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv

from modules.stats_repository import StatsRepository

# Matplotlib (graph)
import matplotlib.pyplot as plt

class StatsFrame(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.last_table = None  # pour export CSV
        self._build_ui()

    def _build_ui(self):
        top = ttk.LabelFrame(self, text="Statistiques")
        top.pack(fill="x", padx=10, pady=10)

        ttk.Button(top, text="CA journalier", command=lambda: self.show_ca("jour")).pack(side="left", padx=5, pady=6)
        ttk.Button(top, text="CA mensuel", command=lambda: self.show_ca("mois")).pack(side="left", padx=5, pady=6)
        ttk.Button(top, text="CA annuel", command=lambda: self.show_ca("annee")).pack(side="left", padx=5, pady=6)

        ttk.Button(top, text="Top médicaments", command=self.show_top_meds).pack(side="left", padx=5, pady=6)
        ttk.Button(top, text="Clients fidèles", command=self.show_clients).pack(side="left", padx=5, pady=6)
        ttk.Button(top, text="Péremption (30j)", command=lambda: self.show_peremption(30)).pack(side="left", padx=5, pady=6)

        ttk.Button(top, text="Entrées stock", command=lambda: self.show_stock_moves("entrees")).pack(side="left", padx=5, pady=6)
        ttk.Button(top, text="Sorties stock", command=lambda: self.show_stock_moves("sorties")).pack(side="left", padx=5, pady=6)

        actions = ttk.Frame(self)
        actions.pack(fill="x", padx=10)

        ttk.Button(actions, text="Exporter (CSV)", command=self.export_csv).pack(side="left", pady=6)

        self.output = tk.Text(self, height=20)
        self.output.pack(fill="both", expand=True, padx=10, pady=10)

    def _clear(self):
        self.output.delete("1.0", tk.END)
        self.last_table = None

    def show_ca(self, period):
        self._clear()
        data = StatsRepository.chiffre_affaires(period)
        if not data:
            self.output.insert(tk.END, "Aucune donnée disponible pour cette période.\n")
            return

        periodes = [p for p, _ in data]
        valeurs = [float(v or 0) for _, v in data]

        self.output.insert(tk.END, f"Chiffre d'affaires ({period})\n\n")
        for p, v in data:
            self.output.insert(tk.END, f"{p} : {float(v or 0):.2f} €\n")

        self.last_table = ("CA", ["periode", "chiffre_affaires"], [(p, float(v)) for p, v in zip(periodes, valeurs)])

        plt.figure()
        plt.plot(periodes, valeurs, marker="o")
        plt.title(f"Chiffre d'affaires ({period})")
        plt.xlabel("Période")
        plt.ylabel("€")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

    def show_top_meds(self):
        self._clear()
        data = StatsRepository.medicaments_plus_vendus()
        if not data:
            self.output.insert(tk.END, "Aucune donnée disponible.\n")
            return

        noms = [n for n, _ in data]
        quantites = [int(q or 0) for _, q in data]

        self.output.insert(tk.END, "Médicaments les plus vendus\n\n")
        for nom, q in data:
            self.output.insert(tk.END, f"{nom} : {int(q or 0)}\n")

        self.last_table = ("TopMedicaments", ["nom", "quantite_vendue"], list(zip(noms, quantites)))

        plt.figure()
        plt.bar(noms, quantites)
        plt.title("Top médicaments vendus")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

    def show_clients(self):
        self._clear()
        data = StatsRepository.clients_fideles()
        if not data:
            self.output.insert(tk.END, "Aucune donnée disponible.\n")
            return

        self.output.insert(tk.END, "Clients les plus fidèles\n\n")
        rows = []
        for nom, prenom, nb in data:
            nb = int(nb or 0)
            self.output.insert(tk.END, f"{prenom} {nom} : {nb} achats\n")
            rows.append((nom, prenom, nb))

        self.last_table = ("ClientsFideles", ["nom", "prenom", "nb_achats"], rows)

    def show_peremption(self, jours=30):
        self._clear()
        data = StatsRepository.medicaments_proches_peremption(jours)
        if not data:
            self.output.insert(tk.END, f"Aucun médicament proche de péremption sous {jours} jours.\n")
            return

        self.output.insert(tk.END, f"Médicaments proches de la péremption (<= {jours} jours)\n\n")
        rows = []
        for nom, datep in data:
            self.output.insert(tk.END, f"{nom} : {datep}\n")
            rows.append((nom, datep))

        self.last_table = ("Peremption", ["nom", "date_peremption"], rows)

    def show_stock_moves(self, mode: str):
        self._clear()
        if mode == "entrees":
            data = StatsRepository.entrees_stock("jour")
            title = "Entrées de stock (par jour)"
            headers = ["periode", "total_entrees"]
            name = "EntreesStock"
        else:
            data = StatsRepository.sorties_stock("jour")
            title = "Sorties de stock (par jour)"
            headers = ["periode", "total_sorties"]
            name = "SortiesStock"

        if not data:
            self.output.insert(tk.END, "Aucune donnée disponible.\n")
            return

        self.output.insert(tk.END, f"{title}\n\n")
        periodes = [p for p, _ in data]
        valeurs = [int(v or 0) for _, v in data]
        for p, v in zip(periodes, valeurs):
            self.output.insert(tk.END, f"{p} : {v}\n")

        self.last_table = (name, headers, list(zip(periodes, valeurs)))

        plt.figure()
        plt.plot(periodes, valeurs, marker="o")
        plt.title(title)
        plt.xlabel("Période")
        plt.ylabel("Quantité")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

    def export_csv(self):
        if not self.last_table:
            messagebox.showwarning("Attention", "Aucune table à exporter. Lance une statistique d’abord.")
            return

        name, headers, rows = self.last_table
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile=f"{name}.csv"
        )
        if not path:
            return

        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f, delimiter=";")
                w.writerow(headers)
                for r in rows:
                    w.writerow(list(r))
            messagebox.showinfo("Export OK", f"Fichier créé :\n{path}")
        except Exception as e:
            messagebox.showerror("Erreur", str(e))
