import tkinter as tk

from database.db import init_db
from modules.sales_view import SalesFrame
from utils.window import autosize_and_center


def main():
    init_db()
    root = tk.Tk()
    root.title("Vente libre - Test")

    frame = SalesFrame(root)
    frame.pack(fill="both", expand=True)

    autosize_and_center(root, min_w=1100, min_h=750)
    root.mainloop()


if __name__ == "__main__":
    main()
