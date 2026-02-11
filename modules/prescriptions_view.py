import os
import subprocess
import sys
import tkinter as tk
from datetime import datetime
from tkinter import ttk, messagebox, filedialog

from modules.prescriptions_repository import PrescriptionsRepository


class PrescriptionsFrame(ttk.Frame):
    """
    - Client: recherche nom/prenom/secu/tel (mode DB), ou imposé par la MainWindow (mode on_validate)
    - Médecin et date ordonnance obligatoires
    - Numéro ordonnance supprimé
    - Pièces jointes: ajout + aperçu
    """

    def __init__(self, master, on_validate=None, client_from_main=None):
        super().__init__(master)
        self.on_validate = on_validate

        self.cart = []

        # Client
        self.client_id = None
        self.client_data = None  # (id, nom, prenom, telephone, email, carte_fidelite)
        self.client_label_var = tk.StringVar(value="Client : (non associé)")

        # Attachments
        self.attachments = []

        # Si mode "push vers main": client obligatoire venant de la main
        if self.on_validate is not None:
            if not client_from_main or not client_from_main.get("id"):
                self.client_label_var.set("Client : (à sélectionner dans la fenêtre principale)")
            else:
                self.client_id = int(client_from_main["id"])
                self.client_data = (
                    int(client_from_main["id"]),
                    client_from_main.get("nom", ""),
                    client_from_main.get("prenom", ""),
                    client_from_main.get("telephone", ""),
                    "",
                    "",
                )
                self.client_label_var.set(
                    f"Client : {self.client_data[2]} {self.client_data[1]} ({self.client_data[3]})".strip()
                )

        self._build_ui()
        self.refresh_medicaments()
        self.refresh_cart()
        self.refresh_attachments()

    def _build_ui(self):
        top = ttk.LabelFrame(self, text="Informations ordonnance + client (obligatoire)")
        top.pack(fill="x", padx=10, pady=10)

        row1 = ttk.Frame(top)
        row1.pack(fill="x", padx=8, pady=6)

        if self.on_validate is None:
            ttk.Label(row1, text="Recherche client (nom/prénom/sécu/tel) :").pack(side="left")
            self.client_search_var = tk.StringVar()
            ttk.Entry(row1, textvariable=self.client_search_var, width=28).pack(side="left", padx=6)
            ttk.Button(row1, text="Rechercher client", command=self.attach_client).pack(side="left")
        else:
            ttk.Label(row1, text="Client (depuis la fenêtre principale) :").pack(side="left")

        ttk.Label(row1, textvariable=self.client_label_var).pack(side="left", padx=(15, 0))

        ttk.Button(row1, text="Ajouter scan/fichier", command=self.add_attachment).pack(side="right")

        row_files = ttk.Frame(top)
        row_files.pack(fill="x", padx=8, pady=(0, 6))

        ttk.Label(row_files, text="Fichiers :").pack(side="left")
        self.files_list = tk.Listbox(row_files, height=3)
        self.files_list.pack(side="left", fill="x", expand=True, padx=6)
        self.files_list.bind("<Double-Button-1>", lambda _e: self.preview_selected_attachment())

        ttk.Button(row_files, text="Aperçu", command=self.preview_selected_attachment).pack(side="left")
        ttk.Button(row_files, text="Retirer", command=self.remove_selected_attachment).pack(side="left", padx=6)

        row2 = ttk.Frame(top)
        row2.pack(fill="x", padx=8, pady=6)

        ttk.Label(row2, text="Médecin (obligatoire) :").pack(side="left")
        self.medecin_var = tk.StringVar()
        ttk.Entry(row2, textvariable=self.medecin_var, width=24).pack(side="left", padx=6)

        ttk.Label(row2, text="Date ordonnance (YYYY-MM-DD, obligatoire) :").pack(side="left", padx=(15, 0))
        self.date_var = tk.StringVar()
        ttk.Entry(row2, textvariable=self.date_var, width=14).pack(side="left", padx=6)

        main = ttk.Frame(self)
        main.pack(fill="both", expand=True, padx=10, pady=5)

        left = ttk.LabelFrame(main, text="Médicaments")
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        search_bar = ttk.Frame(left)
        search_bar.pack(fill="x", padx=8, pady=8)

        ttk.Label(search_bar, text="Recherche :").pack(side="left")
        self.med_search_var = tk.StringVar()
        e = ttk.Entry(search_bar, textvariable=self.med_search_var, width=35)
        e.pack(side="left", padx=8)
        e.bind("<Return>", lambda _e: self.refresh_medicaments())
        ttk.Button(search_bar, text="Rechercher", command=self.refresh_medicaments).pack(side="left")
        ttk.Button(search_bar, text="Tout afficher", command=self._clear_med_search).pack(side="left", padx=6)

        cols = ("id", "code", "nom", "dosage", "prix", "stock", "peremption")
        self.meds_tree = ttk.Treeview(left, columns=cols, show="headings", height=14)
        for c, t, w in [
            ("id", "ID", 50),
            ("code", "Code", 110),
            ("nom", "Nom", 220),
            ("dosage", "Dosage", 100),
            ("prix", "Prix", 80),
            ("stock", "Stock", 70),
            ("peremption", "Péremption", 110),
        ]:
            self.meds_tree.heading(c, text=t)
            self.meds_tree.column(c, width=w, anchor="center" if c in ("id", "prix", "stock") else "w")
        self.meds_tree.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        add_box = ttk.Frame(left)
        add_box.pack(fill="x", padx=8, pady=(0, 8))

        ttk.Label(add_box, text="Quantité :").pack(side="left")
        self.qty_var = tk.StringVar(value="1")
        ttk.Entry(add_box, textvariable=self.qty_var, width=6).pack(side="left", padx=6)
        ttk.Button(add_box, text="Ajouter à l'ordonnance", command=self.add_to_cart).pack(side="left")

        right = ttk.LabelFrame(main, text="Ordonnance - panier")
        right.pack(side="left", fill="both", expand=True)

        cart_cols = ("med_id", "code", "nom", "qte", "pu", "st")
        self.cart_tree = ttk.Treeview(right, columns=cart_cols, show="headings", height=12)
        for c, t, w in [
            ("med_id", "ID", 50),
            ("code", "Code", 110),
            ("nom", "Médicament", 220),
            ("qte", "Qté", 50),
            ("pu", "PU", 70),
            ("st", "Sous-total", 90),
        ]:
            self.cart_tree.heading(c, text=t)
            self.cart_tree.column(c, width=w, anchor="center" if c in ("med_id", "qte", "pu", "st") else "w")
        self.cart_tree.pack(fill="both", expand=True, padx=8, pady=8)

        actions = ttk.Frame(right)
        actions.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(actions, text="Modifier quantité", command=self.update_cart_qty).pack(side="left")
        ttk.Button(actions, text="Supprimer ligne", command=self.remove_cart_line).pack(side="left", padx=6)
        ttk.Button(actions, text="Vider", command=self.clear_cart).pack(side="left")

        bottom = ttk.LabelFrame(self, text="Validation")
        bottom.pack(fill="x", padx=10, pady=10)

        rowc = ttk.Frame(bottom)
        rowc.pack(fill="x", padx=8, pady=8)

        ttk.Button(rowc, text="Valider l'ordonnance", command=self.validate_prescription).pack(side="left")

    # ================= Attachments =================

    def add_attachment(self):
        path = filedialog.askopenfilename(
            parent=self.winfo_toplevel(),
            title="Ajouter un scan/fichier",
            filetypes=[
                ("PDF", "*.pdf"),
                ("Images", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("Tous les fichiers", "*.*"),
            ],
        )
        if not path:
            return
        path = os.path.abspath(path)
        if path not in self.attachments:
            self.attachments.append(path)
        self.refresh_attachments()

    def refresh_attachments(self):
        self.files_list.delete(0, tk.END)
        for p in self.attachments:
            self.files_list.insert(tk.END, os.path.basename(p))

    def _get_selected_attachment_index(self):
        sel = self.files_list.curselection()
        if not sel:
            return None
        return int(sel[0])

    def preview_selected_attachment(self):
        idx = self._get_selected_attachment_index()
        if idx is None:
            messagebox.showwarning("Attention", "Sélectionnez un fichier dans la liste.")
            return
        path = self.attachments[idx]
        if not os.path.exists(path):
            messagebox.showerror("Erreur", "Fichier introuvable (chemin invalide).")
            return
        try:
            if sys.platform.startswith("darwin"):
                subprocess.Popen(["open", path])
            elif os.name == "nt":
                os.startfile(path)  # type: ignore[attr-defined]
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le fichier : {e}")

    def remove_selected_attachment(self):
        idx = self._get_selected_attachment_index()
        if idx is None:
            messagebox.showwarning("Attention", "Sélectionnez un fichier à retirer.")
            return
        del self.attachments[idx]
        self.refresh_attachments()

    # ================= Ordonnance =================

    def _clear_med_search(self):
        self.med_search_var.set("")
        self.refresh_medicaments()

    def refresh_medicaments(self):
        for it in self.meds_tree.get_children():
            self.meds_tree.delete(it)
        rows = PrescriptionsRepository.search_medicaments(self.med_search_var.get())
        for r in rows:
            self.meds_tree.insert("", "end", values=r)

    def attach_client(self):
        q = (self.client_search_var.get() or "").strip()
        if not q:
            messagebox.showwarning("Attention", "Entrez un nom/prénom/sécu/tel.")
            return
        c = PrescriptionsRepository.find_client(q)
        if not c:
            messagebox.showerror("Erreur", "Aucun client trouvé.")
            return
        self.client_data = c
        self.client_id = int(c[0])
        self.client_label_var.set(f"Client : {c[2]} {c[1]} ({c[3]})".strip())
        messagebox.showinfo("OK", "Client associé.")

    def refresh_cart(self):
        for it in self.cart_tree.get_children():
            self.cart_tree.delete(it)

        for line in self.cart:
            st = float(line["quantite"]) * float(line["prix_unitaire"])
            self.cart_tree.insert(
                "",
                "end",
                values=(
                    line["medicament_id"],
                    line.get("code", ""),
                    line["nom"],
                    line["quantite"],
                    f'{float(line["prix_unitaire"]):.2f}',
                    f"{st:.2f}",
                ),
            )

    def add_to_cart(self):
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

        prix = 0.0  # remboursé 100%

        for line in self.cart:
            if line["medicament_id"] == med_id:
                new_q = int(line["quantite"]) + q
                if new_q > stock:
                    messagebox.showerror("Erreur", f"Stock insuffisant (disponible : {stock}).")
                    return
                line["quantite"] = new_q
                self.refresh_cart()
                return

        self.cart.append({"medicament_id": med_id, "code": code, "nom": nom, "quantite": q, "prix_unitaire": prix})
        self.refresh_cart()

    def _get_selected_cart_index(self):
        sel = self.cart_tree.selection()
        if not sel:
            return None
        values = self.cart_tree.item(sel[0], "values")
        med_id = int(values[0])
        for i, line in enumerate(self.cart):
            if line["medicament_id"] == med_id:
                return i
        return None

    def update_cart_qty(self):
        idx = self._get_selected_cart_index()
        if idx is None:
            messagebox.showwarning("Attention", "Sélectionnez une ligne.")
            return

        win = tk.Toplevel(self)
        win.title("Modifier quantité")
        win.resizable(False, False)

        ttk.Label(win, text="Nouvelle quantité :").pack(padx=10, pady=(10, 4))
        var = tk.StringVar(value=str(self.cart[idx]["quantite"]))
        ttk.Entry(win, textvariable=var, width=10).pack(padx=10, pady=4)

        def apply():
            try:
                q = int(var.get())
            except Exception:
                messagebox.showerror("Erreur", "Quantité invalide.")
                return
            if q <= 0:
                messagebox.showerror("Erreur", "Quantité doit être > 0.")
                return
            self.cart[idx]["quantite"] = q
            win.destroy()
            self.refresh_cart()

        ttk.Button(win, text="Valider", command=apply).pack(padx=10, pady=(6, 10))

    def remove_cart_line(self):
        idx = self._get_selected_cart_index()
        if idx is None:
            messagebox.showwarning("Attention", "Sélectionnez une ligne.")
            return
        del self.cart[idx]
        self.refresh_cart()

    def clear_cart(self):
        if not self.cart:
            return
        if not messagebox.askyesno("Confirmation", "Vider l'ordonnance ?"):
            return
        self.cart = []
        self.refresh_cart()

    def validate_prescription(self):
        # Client obligatoire (main obligatoire en mode on_validate)
        if self.on_validate is not None:
            if not self.client_data or not self.client_id:
                messagebox.showerror("Erreur", "Sélectionnez obligatoirement un client dans la fenêtre principale.")
                return
        else:
            if not self.client_id:
                messagebox.showerror("Erreur", "Client obligatoire pour une ordonnance.")
                return

        if not self.cart:
            messagebox.showwarning("Attention", "Ordonnance vide.")
            return

        medecin = (self.medecin_var.get() or "").strip()
        if not medecin:
            messagebox.showerror("Erreur", "Le médecin est obligatoire.")
            return

        date_ord = (self.date_var.get() or "").strip()
        if not date_ord:
            messagebox.showerror("Erreur", "La date de l'ordonnance est obligatoire.")
            return
        try:
            datetime.strptime(date_ord, "%Y-%m-%d")
        except Exception:
            messagebox.showerror("Erreur", "Date invalide. Format attendu : YYYY-MM-DD.")
            return

        if not messagebox.askyesno("Confirmation", "Valider l'ordonnance ?"):
            return

        info = {
            "numero": "",  # supprimé
            "medecin": medecin,
            "date_ordonnance": date_ord,
            "date_saisie": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "files": list(self.attachments),
        }

        if self.on_validate is not None:
            client = {
                "id": int(self.client_data[0]),
                "nom": self.client_data[1],
                "prenom": self.client_data[2],
                "telephone": self.client_data[3],
            }
            lines = []
            for line in self.cart:
                lines.append(
                    {
                        "medicament_id": int(line["medicament_id"]),
                        "code": line.get("code", ""),
                        "nom": line.get("nom", ""),
                        "quantite": int(line["quantite"]),
                        "prix_unitaire": 0.0,
                        "ordonnance": True,
                    }
                )
            self.on_validate(client, info, lines)
            self.winfo_toplevel().destroy()
            return

        # Mode DB (enregistre directement)
        try:
            PrescriptionsRepository.create_prescription_sale(
                client_id=self.client_id,
                ordonnance_info=info,
                cart_lines=self.cart,
                remise=0.0,
                user_id=None,
            )
            messagebox.showinfo("Succès", "Ordonnance enregistrée.")
        except Exception as e:
            messagebox.showerror("Erreur", str(e))
