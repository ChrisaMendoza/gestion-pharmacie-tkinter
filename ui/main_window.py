import os
import subprocess
import sys
import tkinter as tk
from datetime import datetime
from tkinter import ttk, messagebox

from ui.stock_ui import StockUI
from ui.select_medicament_ui import SelectMedicamentUI
from ui.client_picker_ui import ClientPickerUI
from ui.ordonnance_history_ui import OrdonnanceHistoryUI

from modules.prescriptions_view import PrescriptionsFrame
from modules.sales_repository import SalesRepository
from modules.prescriptions_repository import PrescriptionsRepository
from modules.clients_view import ClientsFrame
from utils.window import autosize_and_center


class MainWindow:
    def __init__(self, user):
        self.user = user

        self.clients_window = None
        self.ord_window = None

        # IMPORTANT: root avant toute variable Tk
        self.root = tk.Tk()
        self.root.title("Système de Gestion de Pharmacie")
        self.root.resizable(True, True)

        # ===== Client associé =====
        self.selected_client_id = None
        self.client_nom_var = tk.StringVar(master=self.root, value="")
        self.client_prenom_var = tk.StringVar(master=self.root, value="")
        self.client_tel_var = tk.StringVar(master=self.root, value="")
        self.client_dn_var = tk.StringVar(master=self.root, value="")
        self.client_secu_var = tk.StringVar(master=self.root, value="")
        self.client_label_var = tk.StringVar(master=self.root, value="Client : (aucun)")

        # ===== Panier (mixte) =====
        self.cart_lines = []

        # ===== Infos ordonnance (affichées côté main après validation ordonnance) =====
        self.ord_medecin_var = tk.StringVar(master=self.root, value="")
        self.ord_date_var = tk.StringVar(master=self.root, value="")
        self.ord_date_saisie_var = tk.StringVar(master=self.root, value="")
        self.ord_files = []  # list[str] chemins absolus

        # ===== Finalisation =====
        self.remise_var = tk.StringVar(master=self.root, value="0")
        self.total_var = tk.StringVar(master=self.root, value="Total : 0.00 €")
        self.last_sale_id = None
        self.last_ordonnance_id = None

        main_frame = tk.Frame(self.root)
        main_frame.pack(expand=True, fill="both", padx=10, pady=10)

        # ================= FRAME HAUT =================
        top_frame = tk.Frame(main_frame)
        top_frame.pack(fill="x")

        # ----- CLIENT -----
        client_frame = tk.LabelFrame(top_frame, text="Client")
        client_frame.pack(side="left", expand=True, fill="both", padx=5)

        tk.Label(client_frame, textvariable=self.client_label_var, fg="gray").pack(
            anchor="w", padx=10, pady=(10, 0)
        )

        form = ttk.Frame(client_frame)
        form.pack(fill="x", padx=10, pady=10)

        self._ro_field(form, "Nom", self.client_nom_var, 0, 0)
        self._ro_field(form, "Prénom", self.client_prenom_var, 0, 2)
        self._ro_field(form, "Téléphone", self.client_tel_var, 1, 0)
        self._ro_field(form, "Naissance", self.client_dn_var, 1, 2)
        self._ro_field(form, "Sécu", self.client_secu_var, 2, 0)

        form.grid_columnconfigure(1, weight=1)
        form.grid_columnconfigure(3, weight=1)

        btns = ttk.Frame(client_frame)
        btns.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(btns, text="Associer / Créer", command=self.open_client_picker).pack(side="left")
        ttk.Button(btns, text="Désassocier", command=self.detach_client).pack(side="left", padx=6)
        ttk.Button(btns, text="Gestion clients", command=self.open_clients).pack(side="right")

        # ----- ORDONNANCE -----
        ord_frame = tk.LabelFrame(top_frame, text="Ordonnance")
        ord_frame.pack(side="left", expand=True, fill="both", padx=5)

        info = ttk.LabelFrame(ord_frame, text="Dernière ordonnance validée")
        info.pack(fill="x", padx=10, pady=(6, 6))

        row1 = ttk.Frame(info)
        row1.pack(fill="x", padx=8, pady=6)
        ttk.Label(row1, text="Prescripteur :").pack(side="left")
        ttk.Entry(row1, textvariable=self.ord_medecin_var, state="readonly", width=26).pack(
            side="left", padx=6
        )

        ttk.Label(row1, text="Date ordonnance :").pack(side="left", padx=(12, 0))
        ttk.Entry(row1, textvariable=self.ord_date_var, state="readonly", width=14).pack(side="left", padx=6)

        row2 = ttk.Frame(info)
        row2.pack(fill="x", padx=8, pady=(0, 6))
        ttk.Label(row2, text="Date saisie :").pack(side="left")
        ttk.Entry(row2, textvariable=self.ord_date_saisie_var, state="readonly", width=20).pack(
            side="left", padx=6
        )

        row3 = ttk.Frame(info)
        row3.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Label(row3, text="Fichiers :").pack(side="left")
        self.ord_files_list = tk.Listbox(row3, height=3)
        self.ord_files_list.pack(side="left", fill="x", expand=True, padx=6)
        self.ord_files_list.bind("<Double-Button-1>", lambda _e: self.preview_selected_ord_file())
        ttk.Button(row3, text="Aperçu", command=self.preview_selected_ord_file).pack(side="left")

        # Boutons (sous les fichiers) : Traiter + Historique à droite
        ord_actions = ttk.Frame(ord_frame)
        ord_actions.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(ord_actions, text="Traiter l'ordonnance", command=self.open_prescriptions).pack(side="left")
        ttk.Button(ord_actions, text="Historique ordonnances", command=self.open_ordonnance_history).pack(
            side="left", padx=10
        )

        # ================= FRAME BAS =================
        bottom_frame = tk.Frame(main_frame)
        bottom_frame.pack(expand=True, fill="both", pady=10)

        # Colonne droite: Administration (haut) + Finalisation (bas)
        side_panel = tk.Frame(bottom_frame)
        side_panel.pack(side="right", fill="y", padx=5)

        # ----- PANIER -----
        vente_frame = tk.LabelFrame(bottom_frame, text="Panier")
        vente_frame.pack(side="left", expand=True, fill="both", padx=5)

        cols = ("ordonnance", "code", "nom", "quantite", "pu", "st")
        self.table = ttk.Treeview(vente_frame, columns=cols, show="headings", height=14)

        self.table.heading("ordonnance", text="Ordonnance")
        self.table.heading("code", text="Code")
        self.table.heading("nom", text="Médicament")
        self.table.heading("quantite", text="Quantité")
        self.table.heading("pu", text="PU (€)")
        self.table.heading("st", text="Sous-total (€)")

        self.table.column("ordonnance", width=95, anchor="center")
        self.table.column("code", width=110, anchor="center")
        self.table.column("nom", width=260)
        self.table.column("quantite", width=80, anchor="center")
        self.table.column("pu", width=90, anchor="center")
        self.table.column("st", width=110, anchor="center")

        self.table.pack(expand=True, fill="both", padx=10, pady=(10, 6))

        btns_cart = tk.Frame(vente_frame)
        btns_cart.pack(fill="x", padx=10, pady=(0, 10))

        tk.Button(btns_cart, text="Ajouter un médicament", command=self.open_selector).pack(side="left")
        tk.Button(btns_cart, text="Supprimer ligne", command=self.remove_selected_line).pack(side="left", padx=6)
        tk.Button(btns_cart, text="Vider panier", command=self.clear_cart).pack(side="left")

        # ----- ADMIN / STOCK (en haut à droite) -----
        admin_frame = tk.LabelFrame(side_panel, text="Administration")
        admin_frame.pack(fill="x")

        tk.Label(admin_frame, text=f"Utilisateur : {self.user['role']}", fg="gray").pack(pady=20)

        if self.user["role"] in ["ADMIN", "PHARMACIEN", "PREPARATEUR"]:
            tk.Button(
                admin_frame,
                text="Ouvrir gestion des stocks",
                width=30,
                height=2,
                command=self.open_stocks,
            ).pack(padx=10, pady=(0, 10))
        else:
            tk.Label(admin_frame, text="Accès stocks non autorisé", fg="red").pack(padx=10, pady=(0, 10))

        # ----- FINALISATION (en dessous des stocks) -----
        finalize = tk.LabelFrame(side_panel, text="Finalisation")
        finalize.pack(fill="x", pady=(10, 0))

        row_r = ttk.Frame(finalize)
        row_r.pack(fill="x", padx=10, pady=(12, 6))
        ttk.Label(row_r, text="Remise (€) :").pack(side="left")
        ttk.Entry(row_r, textvariable=self.remise_var, width=10).pack(side="left", padx=6)
        ttk.Button(row_r, text="Recalculer", command=self.refresh_cart).pack(side="left", padx=6)

        ttk.Label(finalize, textvariable=self.total_var, font=("Arial", 12, "bold")).pack(
            anchor="e", padx=10, pady=(6, 12)
        )

        ttk.Button(finalize, text="Valider l'achat", command=self.validate_sale).pack(
            fill="x", padx=10, pady=(0, 6)
        )
        ttk.Button(finalize, text="Générer la facture", command=self.generate_invoice).pack(
            fill="x", padx=10, pady=(0, 12)
        )

        self.refresh_cart()
        autosize_and_center(self.root, min_w=1350, min_h=760)
        self.root.mainloop()

    def _ro_field(self, parent, label, var, row, col):
        ttk.Label(parent, text=label).grid(row=row, column=col, sticky="w", padx=(0, 6), pady=6)
        ttk.Entry(parent, textvariable=var, state="readonly", width=26).grid(
            row=row, column=col + 1, sticky="ew", pady=6
        )

    # ================= Utils fichier =================

    def _open_file(self, path: str):
        if not path:
            return
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

    # ================= CLIENT =================

    def open_client_picker(self):
        ClientPickerUI(self.root, self.set_selected_client)

    def set_selected_client(self, client: dict):
        self.selected_client_id = int(client["id"])
        self.client_nom_var.set(client.get("nom", ""))
        self.client_prenom_var.set(client.get("prenom", ""))
        self.client_tel_var.set(client.get("telephone", ""))
        self.client_dn_var.set(client.get("date_naissance", ""))
        self.client_secu_var.set(client.get("secu", ""))
        self.client_label_var.set(
            f"Client : {client.get('prenom','')} {client.get('nom','')} (ID {client['id']})".strip()
        )

    def detach_client(self):
        self.selected_client_id = None
        self.client_nom_var.set("")
        self.client_prenom_var.set("")
        self.client_tel_var.set("")
        self.client_dn_var.set("")
        self.client_secu_var.set("")
        self.client_label_var.set("Client : (aucun)")

    # ================= Historique ordonnances =================

    def open_ordonnance_history(self):
        if not self.selected_client_id:
            messagebox.showwarning("Attention", "Sélectionnez d'abord un client dans la fenêtre principale.")
            return
        client_label = f"{self.client_prenom_var.get()} {self.client_nom_var.get()}".strip()
        OrdonnanceHistoryUI(self.root, client_id=int(self.selected_client_id), client_label=client_label)

    # ================= ORDONNANCES =================

    def open_prescriptions(self):
        if self.ord_window and self.ord_window.winfo_exists():
            self.ord_window.focus()
            return

        win = tk.Toplevel(self.root)
        win.title("Ordonnances")

        frame = PrescriptionsFrame(
            win,
            on_validate=self.on_ordonnance_validated,
            client_from_main={
                "id": self.selected_client_id,
                "nom": self.client_nom_var.get(),
                "prenom": self.client_prenom_var.get(),
                "telephone": self.client_tel_var.get(),
            },
        )
        frame.pack(fill="both", expand=True)

        autosize_and_center(win, min_w=1200, min_h=750)

        self.ord_window = win
        win.protocol("WM_DELETE_WINDOW", lambda: self._close_prescriptions(win))

    def _close_prescriptions(self, win):
        win.destroy()
        if self.ord_window == win:
            self.ord_window = None

    def _refresh_ord_files_list(self):
        self.ord_files_list.delete(0, tk.END)
        for p in self.ord_files:
            self.ord_files_list.insert(tk.END, os.path.basename(p))

    def preview_selected_ord_file(self):
        sel = self.ord_files_list.curselection()
        if not sel:
            messagebox.showwarning("Attention", "Sélectionnez un fichier.")
            return
        idx = int(sel[0])
        if idx < 0 or idx >= len(self.ord_files):
            return
        self._open_file(self.ord_files[idx])

    def on_ordonnance_validated(self, client: dict, ordonnance_info: dict, lines: list[dict]):
        # (optionnel) re-associe le client dans la main
        if client and client.get("id"):
            self.selected_client_id = int(client["id"])
            self.client_nom_var.set(client.get("nom", ""))
            self.client_prenom_var.set(client.get("prenom", ""))
            self.client_tel_var.set(client.get("telephone", ""))
            self.client_label_var.set(
                f"Client : {client.get('prenom','')} {client.get('nom','')} (ID {client['id']})".strip()
            )

        # Affiche infos ordonnance (après validation dans la fenêtre ordonnance)
        med = (ordonnance_info.get("medecin") or "").strip()
        dt = (ordonnance_info.get("date_ordonnance") or "").strip()
        ds = (ordonnance_info.get("date_saisie") or "").strip() or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        files = ordonnance_info.get("files") or []

        self.ord_medecin_var.set(med)
        self.ord_date_var.set(dt)
        self.ord_date_saisie_var.set(ds)
        self.ord_files = list(files)
        self._refresh_ord_files_list()

        # Ajoute les lignes ordonnance au panier main (prix=0)
        for line in lines:
            self._merge_line_into_cart(
                {
                    "medicament_id": int(line["medicament_id"]),
                    "code": line.get("code", ""),
                    "nom": line.get("nom", ""),
                    "quantite": int(line.get("quantite", 0)),
                    "prix_unitaire": 0.0,
                    "ordonnance": True,
                }
            )

        self.refresh_cart()

    # ================= PANIER =================

    def open_selector(self):
        SelectMedicamentUI(self.root, self.add_manual_to_cart)

    def add_manual_to_cart(self, med_tuple):
        # med_tuple = (id, code, nom, prix, stock)
        med_id, code, nom, prix, _stock = med_tuple
        self._merge_line_into_cart(
            {
                "medicament_id": int(med_id),
                "code": str(code),
                "nom": str(nom),
                "quantite": 1,
                "prix_unitaire": float(prix),
                "ordonnance": False,
            }
        )
        self.refresh_cart()

    def _merge_line_into_cart(self, new_line: dict):
        # merge si même medicament_id ET même ordonnance flag
        for line in self.cart_lines:
            if (
                    int(line["medicament_id"]) == int(new_line["medicament_id"])
                    and bool(line["ordonnance"]) == bool(new_line["ordonnance"])
            ):
                line["quantite"] = int(line["quantite"]) + int(new_line["quantite"])
                return
        self.cart_lines.append(new_line)

    def refresh_cart(self):
        self.table.delete(*self.table.get_children())

        total_brut = 0.0
        for line in self.cart_lines:
            q = int(line["quantite"])
            pu = float(line["prix_unitaire"])
            st = q * pu
            total_brut += st

            self.table.insert(
                "",
                "end",
                values=(
                    "Oui" if line.get("ordonnance") else "Non",
                    line.get("code", ""),
                    line.get("nom", ""),
                    q,
                    f"{pu:.2f}",
                    f"{st:.2f}",
                ),
            )

        try:
            remise = float(self.remise_var.get() or 0.0)
        except Exception:
            remise = 0.0

        total_net = max(0.0, total_brut - remise)
        self.total_var.set(f"Total : {total_net:.2f} €")

    def remove_selected_line(self):
        sel = self.table.selection()
        if not sel:
            return
        idx = self.table.index(sel[0])
        if 0 <= idx < len(self.cart_lines):
            del self.cart_lines[idx]
        self.refresh_cart()

    def clear_cart(self):
        if not self.cart_lines:
            return
        if not messagebox.askyesno("Confirmation", "Vider le panier ?"):
            return
        self.cart_lines = []
        self.remise_var.set("0")
        self.refresh_cart()

    # ================= VALIDATION + FACTURE =================

    def validate_sale(self):
        if not self.cart_lines:
            messagebox.showwarning("Attention", "Panier vide")
            return

        try:
            remise = float(self.remise_var.get() or 0.0)
        except Exception:
            messagebox.showerror("Erreur", "Remise invalide.")
            return
        if remise < 0:
            messagebox.showerror("Erreur", "La remise ne peut pas être négative.")
            return

        has_ord = any(bool(l.get("ordonnance")) for l in self.cart_lines)

        if has_ord and not self.selected_client_id:
            messagebox.showerror("Erreur", "Client obligatoire si le panier contient une ordonnance.")
            return

        if not messagebox.askyesno("Confirmation", "Valider et enregistrer ?"):
            return

        user_id = self.user.get("id")

        try:
            if has_ord:
                info = {
                    "numero": "",
                    "medecin": self.ord_medecin_var.get(),
                    "date_ordonnance": self.ord_date_var.get(),
                    "date_saisie": self.ord_date_saisie_var.get() or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "files": list(self.ord_files),
                }
                ord_id, vente_id = PrescriptionsRepository.create_prescription_sale(
                    client_id=int(self.selected_client_id),
                    ordonnance_info=info,
                    cart_lines=self.cart_lines,
                    remise=remise,
                    user_id=user_id,
                )
                self.last_ordonnance_id = ord_id
                self.last_sale_id = vente_id
                messagebox.showinfo("Succès", f"Enregistré: Ordonnance #{ord_id} + Vente #{vente_id}.")
            else:
                vente_id = SalesRepository.create_sale(
                    cart_lines=self.cart_lines,
                    remise=remise,
                    client_id=int(self.selected_client_id) if self.selected_client_id else None,
                    user_id=user_id,
                )
                self.last_ordonnance_id = None
                self.last_sale_id = vente_id
                messagebox.showinfo("Succès", f"Vente enregistrée (ID : {vente_id}).")

            self.cart_lines = []
            self.remise_var.set("0")
            self.refresh_cart()

        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def generate_invoice(self):
        if not self.last_sale_id:
            messagebox.showwarning("Attention", "Aucune vente validée.")
            return
        try:
            if self.last_ordonnance_id:
                ticket_path, facture_path = PrescriptionsRepository.save_docs_to_files(
                    self.last_ordonnance_id, self.last_sale_id
                )
                messagebox.showinfo("Documents générés", f"Ticket :\n{ticket_path}\n\nFacture :\n{facture_path}")
            else:
                facture_path = SalesRepository.save_invoice_to_file(self.last_sale_id)
                messagebox.showinfo("Facture générée", f"Facture :\n{facture_path}")
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    # ================= AUTRES FENÊTRES =================

    def open_stocks(self):
        StockUI(self.root, self.user)

    def open_clients(self):
        if self.clients_window and self.clients_window.winfo_exists():
            self.clients_window.focus()
            return
        win = tk.Toplevel(self.root)
        win.title("Gestion des clients")
        frame = ClientsFrame(win)
        frame.pack(fill="both", expand=True)
        autosize_and_center(win, min_w=950, min_h=650)
        self.clients_window = win
        win.protocol("WM_DELETE_WINDOW", lambda: self._close_clients(win))

    def _close_clients(self, win):
        win.destroy()
        if self.clients_window == win:
            self.clients_window = None
