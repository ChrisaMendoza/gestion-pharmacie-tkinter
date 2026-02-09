import tkinter as tk
from database.db import init_db
from ui.login_ui import LoginUI
from database.db import init_db, create_default_users

init_db()
create_default_users()


if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    LoginUI(root)
    root.mainloop()

