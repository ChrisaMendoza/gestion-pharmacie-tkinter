import tkinter as tk
from database.db import init_db
from modules.clients_view import ClientsFrame

def main():
    init_db()
    root = tk.Tk()
    root.title("Gestion clients - Test")
    root.geometry("950x700")

    frame = ClientsFrame(root)
    frame.pack(fill="both", expand=True)

    root.mainloop()

if __name__ == "__main__":
    main()
