import os
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, messagebox

from modules.prescriptions_repository import PrescriptionsRepository
from utils.window import autosize_and_center


class OrdonnanceHistoryUI:
    def __init__(self, master, client_id: int, client_label: str = ""):
        self.client_id = int(client_id)
        self.client_label = client_label

        self.win = tk.Toplevel(master)
        self.win.title(f"Historique ordonnances - {self.client_label}".strip(" -"))
        self.win.resizable(True, True)

        top = ttk.Frame(self.win)
        top.pack(fill="x", padx=10, pady=10)

        ttk.Label(
            top,
            text=f"Client : {self.client_label} (ID {self.client_id})".strip(),
            foreground="gray",
        ).pack(side="left")

        ttk.Button(top, text="Rafraîchir", command=self.refresh).pack(side="right")

        main = ttk.Frame(self.win)
        main.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        cols = ("id", "medecin", "date_ord", "date_saisie", "fichier")
        self.tree = ttk.Treeview(main, columns=cols, show="headings", height=14)

        self.tree.heading("id", text="ID")
        self.tree.heading("medecin", text="Prescripteur")
        self.tree.heading("date_ord", text="Date ordonnance")
        self.tree.heading("date_saisie", text="Date saisie")
        self.tree.heading("fichier", text="Fichier")

        self.tree.column("id", width=70, anchor="center")
        self.tree.column("medecin", width=220)
        self.tree.column("date_ord", width=120, anchor="center")
        self.tree.column("date_saisie", width=160, anchor="center")
        self.tree.column("fichier", width=260)

        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-Button-1>", lambda _e: self.preview_selected_file())

        actions = ttk.Frame(self.win)
        actions.pack(fill="x", padx=10, pady=(0, 10))

        ttk.Button(actions, text="Voir fichier", command=self.preview_selected_file).pack(side="left")

        autosize_and_center(self.win, min_w=900, min_h=520)
        self.refresh()

    def _open_file(self, path: str):
        if not path:
            return
        if not os.path.exists(path):
            messagebox.showerror("Erreur", "Fichier introuvable (chemin invalide).", parent=self.win)
            return
        try:
            if sys.platform.startswith("darwin"):
                subprocess.Popen(["open", path])
            elif os.name == "nt":
                os.startfile(path)  # type: ignore[attr-defined]
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le fichier : {e}", parent=self.win)

    def _get_selected_row(self):
        sel = self.tree.selection()
        if not sel:
            return None
        return self.tree.item(sel[0], "values")

    def preview_selected_file(self):
        row = self._get_selected_row()
        if not row:
            messagebox.showwarning("Attention", "Sélectionnez une ordonnance.", parent=self.win)
            return

        oid = int(row[0])
        data = PrescriptionsRepository.get_ordonnance_by_id(oid)
        if not data:
            messagebox.showerror("Erreur", "Ordonnance introuvable.", parent=self.win)
            return

        files = data.get("files") or []
        if not files:
            messagebox.showinfo("Info", "Aucun fichier associé à cette ordonnance.", parent=self.win)
            return

        self._open_file(files[0])

    def refresh(self):
        for it in self.tree.get_children():
            self.tree.delete(it)

        rows = PrescriptionsRepository.get_ordonnances_by_client(self.client_id)
        for r in rows:
            files = r.get("files") or []
            display_file = os.path.basename(files[0]) if files else ""
            self.tree.insert(
                "",
                "end",
                values=(
                    r.get("id"),
                    r.get("medecin", ""),
                    r.get("date_ordonnance", ""),
                    r.get("date_saisie", ""),
                    display_file,
                ),
            )
