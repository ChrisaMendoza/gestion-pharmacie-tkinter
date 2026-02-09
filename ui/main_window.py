import tkinter as tk
from tkinter import ttk, messagebox
from ui.stock_ui import StockUI
from ui.select_medicament_ui import SelectMedicamentUI
from services.stock_service import sortie_stock_vente
from modules.clients_view import ClientsFrame
from modules.prescriptions_view import PrescriptionsFrame


class MainWindow:
    def __init__(self, user):
        self.user = user
        self.cart = {}
        self.clients_window = None
        self.ord_window = None

        self.root = tk.Tk()
        self.root.title("Système de Gestion de Pharmacie")
        self.root.geometry("1400x800")

        main_frame = tk.Frame(self.root)
        main_frame.pack(expand=True, fill="both", padx=10, pady=10)

        # ================= FRAME HAUT =================
        top_frame = tk.Frame(main_frame)
        top_frame.pack(fill="x")

        # ----- CLIENTS -----
        clients_frame = tk.LabelFrame(top_frame, text="Gestion des clients")
        clients_frame.pack(side="left", expand=True, fill="both", padx=5)

        tk.Label(
            clients_frame,
            text="Module clients\n(implémenté par collègue)",
            fg="gray"
        ).pack(expand=True)

        tk.Button(
            clients_frame,
            text="Ouvrir gestion clients",
            command=self.open_clients
        ).pack(pady=10)

        # ----- ORDONNANCES -----
        ord_frame = tk.LabelFrame(top_frame, text="Ordonnances")
        ord_frame.pack(side="left", expand=True, fill="both", padx=5)

        tk.Label(
            ord_frame,
            text="Module ordonnances\n(implémenté par collègue)",
            fg="gray"
        ).pack(expand=True)

        tk.Button(
            ord_frame,
            text="Traiter ordonnance",
            command=self.open_prescriptions
        ).pack(pady=10)

        # ================= FRAME BAS =================
        bottom_frame = tk.Frame(main_frame)
        bottom_frame.pack(expand=True, fill="both", pady=10)

        # ----- VENTE -----
        vente_frame = tk.LabelFrame(bottom_frame, text="Vente / Panier")
        vente_frame.pack(side="left", expand=True, fill="both", padx=5)

        self.table = ttk.Treeview(
            vente_frame,
            columns=("code", "nom", "quantite", "prix"),
            show="headings"
        )

        for c, t in {
            "code": "Code",
            "nom": "Médicament",
            "quantite": "Quantité",
            "prix": "Prix (€)"
        }.items():
            self.table.heading(c, text=t)
            self.table.column(c, anchor="center")

        self.table.pack(expand=True, fill="both", padx=10, pady=10)

        btns = tk.Frame(vente_frame)
        btns.pack(fill="x")

        tk.Button(
            btns,
            text="Ajouter un médicament",
            command=self.open_selector
        ).pack(side="left", padx=5)

        tk.Button(
            btns,
            text="Supprimer du panier",
            command=self.remove_from_cart
        ).pack(side="left", padx=5)

        tk.Button(
            btns,
            text="Valider la vente",
            bg="#4CAF50",
            fg="white",
            command=self.validate_sale
        ).pack(side="right", padx=5)

        # ----- ADMIN / STOCK -----
        admin_frame = tk.LabelFrame(bottom_frame, text="Administration")
        admin_frame.pack(side="left", expand=True, fill="both", padx=5)

        tk.Label(
            admin_frame,
            text=f"Utilisateur : {self.user['role']}",
            fg="gray"
        ).pack(pady=20)

        if self.user["role"] in ["ADMIN", "PHARMACIEN", "PREPARATEUR"]:
            tk.Button(
                admin_frame,
                text="Ouvrir gestion des stocks",
                width=30,
                height=2,
                command=self.open_stocks
            ).pack()
        else:
            tk.Label(
                admin_frame,
                text="Accès stocks non autorisé",
                fg="red"
            ).pack()

        self.root.mainloop()

    # ================= LOGIQUE =================

    def open_selector(self):
        SelectMedicamentUI(self.root, self.add_to_cart)

    def add_to_cart(self, med):
        med_id, code, nom, prix, stock = med
        self.cart.setdefault(med_id, {"code": code, "nom": nom, "prix": prix, "qte": 0})
        self.cart[med_id]["qte"] += 1
        self.refresh_cart()

    def refresh_cart(self):
        self.table.delete(*self.table.get_children())
        for v in self.cart.values():
            self.table.insert("", "end", values=(v["code"], v["nom"], v["qte"], v["prix"]))

    def remove_from_cart(self):
        sel = self.table.focus()
        if not sel:
            return
        code = self.table.item(sel)["values"][0]
        for k in list(self.cart.keys()):
            if self.cart[k]["code"] == code:
                del self.cart[k]
                break
        self.refresh_cart()

    def validate_sale(self):
        if not self.cart:
            messagebox.showwarning("Attention", "Panier vide")
            return
        try:
            for med_id, item in self.cart.items():
                sortie_stock_vente(med_id, item["qte"])
            self.cart.clear()
            self.refresh_cart()
            messagebox.showinfo("Succès", "Vente validée")
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def open_stocks(self):
        StockUI(self.root, self.user)

    def open_clients(self):
        if self.clients_window and self.clients_window.winfo_exists():
            self.clients_window.focus()
            return
        win = tk.Toplevel(self.root)
        win.title("Gestion des clients")
        win.geometry("950x700")
        frame = ClientsFrame(win)
        frame.pack(fill="both", expand=True)
        self.clients_window = win
        win.protocol("WM_DELETE_WINDOW", lambda: self._close_clients(win))

    def _close_clients(self, win):
        win.destroy()
        if self.clients_window == win:
            self.clients_window = None

    def open_prescriptions(self):
        if self.ord_window and self.ord_window.winfo_exists():
            self.ord_window.focus()
            return
        win = tk.Toplevel(self.root)
        win.title("Ordonnances")
        win.geometry("1250x800")
        frame = PrescriptionsFrame(win)
        frame.pack(fill="both", expand=True)
        self.ord_window = win
        win.protocol("WM_DELETE_WINDOW", lambda: self._close_prescriptions(win))

    def _close_prescriptions(self, win):
        win.destroy()
        if self.ord_window == win:
            self.ord_window = None
