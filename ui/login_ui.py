import tkinter as tk
from tkinter import messagebox

from services.auth_service import authenticate
from ui.main_window import MainWindow
from utils.window import autosize_and_center


class LoginUI:
    def __init__(self, root):
        self.root = root
        root.title("Connexion")
        root.resizable(False, False)

        tk.Label(root, text="Utilisateur").pack(padx=14, pady=(12, 2))
        self.username = tk.Entry(root)
        self.username.pack(padx=14, pady=(0, 8), fill="x")

        tk.Label(root, text="Mot de passe").pack(padx=14, pady=(0, 2))
        self.password = tk.Entry(root, show="*")
        self.password.pack(padx=14, pady=(0, 10), fill="x")

        tk.Button(root, text="Connexion", command=self.login).pack(pady=(0, 12))

        autosize_and_center(root, min_w=320, min_h=220)

    def login(self):
        try:
            user = authenticate(self.username.get(), self.password.get())
            self.root.destroy()
            MainWindow(user)
        except Exception as e:
            messagebox.showerror("Erreur", str(e))
