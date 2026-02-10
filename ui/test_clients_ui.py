import tkinter as tk

from database.db import init_db
from modules.clients_view import ClientsFrame
from utils.window import autosize_and_center


def main():
    init_db()
    root = tk.Tk()
    root.title("Gestion clients - Test")

    frame = ClientsFrame(root)
    frame.pack(fill="both", expand=True)

    autosize_and_center(root, min_w=950, min_h=650)
    root.mainloop()


if __name__ == "__main__":
    main()
