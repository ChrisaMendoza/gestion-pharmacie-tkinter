import tkinter as tk
from database.db import init_db
from modules.prescriptions_view import PrescriptionsFrame

def main():
    init_db()
    root = tk.Tk()
    root.title("Ordonnances - Test")
    root.geometry("1100x780")

    frame = PrescriptionsFrame(root)
    frame.pack(fill="both", expand=True)

    root.mainloop()

if __name__ == "__main__":
    main()
