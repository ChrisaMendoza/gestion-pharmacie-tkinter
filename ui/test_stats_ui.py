import tkinter as tk
from database.db import init_db
from modules.stats_view import StatsFrame

def main():
    init_db()
    root = tk.Tk()
    root.title("Statistiques & rapports - Test")
    root.geometry("900x650")

    frame = StatsFrame(root)
    frame.pack(fill="both", expand=True)

    root.mainloop()

if __name__ == "__main__":
    main()
