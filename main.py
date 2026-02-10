import tkinter as tk

from database.db import init_db, migrate_db, create_default_users
from ui.login_ui import LoginUI


def bootstrap_db():
    init_db()
    migrate_db()
    create_default_users()


if __name__ == "__main__":
    bootstrap_db()
    root = tk.Tk()
    LoginUI(root)
    root.mainloop()