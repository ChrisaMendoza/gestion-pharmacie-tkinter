import tkinter as tk
from tkinter import messagebox
from services.auth_service import authenticate
from ui.main_window import MainWindow

class LoginUI:
    def __init__(self, root):
        self.root = root
        root.title("Connexion")

        tk.Label(root, text="Utilisateur").pack()
        self.username = tk.Entry(root)
        self.username.pack()

        tk.Label(root, text="Mot de passe").pack()
        self.password = tk.Entry(root, show="*")
        self.password.pack()

        tk.Button(root, text="Connexion", command=self.login).pack(pady=10)

    def login(self):
        try:
            user = authenticate(self.username.get(), self.password.get())
            self.root.destroy()
            MainWindow(user)
        except Exception as e:
            messagebox.showerror("Erreur", str(e))
