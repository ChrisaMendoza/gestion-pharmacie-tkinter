def autosize_and_center(win, min_w: int | None = None, min_h: int | None = None):
    win.update_idletasks()
    win.geometry("")  # autosize selon le contenu
    win.update_idletasks()

    w = win.winfo_width()
    h = win.winfo_height()

    if min_w is not None:
        w = max(w, int(min_w))
    if min_h is not None:
        h = max(h, int(min_h))

    if min_w is not None or min_h is not None:
        win.geometry(f"{w}x{h}")
        win.update_idletasks()
        w = win.winfo_width()
        h = win.winfo_height()

    x = (win.winfo_screenwidth() // 2) - (w // 2)
    y = (win.winfo_screenheight() // 2) - (h // 2)
    win.geometry(f"{w}x{h}+{x}+{y}")
