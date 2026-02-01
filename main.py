import tkinter as tk
from database.db import init_db
from ui.login_ui import LoginUI

if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    LoginUI(root)
    root.mainloop()

