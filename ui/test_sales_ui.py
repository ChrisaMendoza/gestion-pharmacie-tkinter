import tkinter as tk
from database.db import init_db
from modules.sales_view import SalesFrame

def main():
    init_db()
    root = tk.Tk()
    root.title("Vente libre - Test")
    root.geometry("1100x750")

    frame = SalesFrame(root)
    frame.pack(fill="both", expand=True)

    root.mainloop()

if __name__ == "__main__":
    main()
