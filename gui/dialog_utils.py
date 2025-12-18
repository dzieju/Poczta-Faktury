"""
Utility functions for dialog window positioning and management
"""
import tkinter as tk
from tkinter import messagebox


def center_and_clamp_window(win: tk.Toplevel, parent: tk.Widget = None, max_ratio: float = 0.95):
    """
    Center and clamp a Toplevel window to the visible screen area.
    
    This function ensures dialog windows:
    - Are sized reasonably (not larger than max_ratio of screen)
    - Are centered relative to parent window (if provided) or screen
    - Stay within visible screen boundaries
    
    Args:
        win: Toplevel window to position
        parent: Parent widget to center relative to (optional)
        max_ratio: Maximum ratio of screen size the window can occupy (default 0.95)
    """
    win.update_idletasks()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    max_w = int(sw * max_ratio)
    max_h = int(sh * max_ratio)
    w = win.winfo_reqwidth() or win.winfo_width()
    h = win.winfo_reqheight() or win.winfo_height()
    resized = False
    if w > max_w:
        w = max_w
        resized = True
    if h > max_h:
        h = max_h
        resized = True
    if resized:
        win.geometry(f"{w}x{h}")
    win.update_idletasks()
    w = win.winfo_width()
    h = win.winfo_height()
    if parent:
        try:
            px = parent.winfo_rootx()
            py = parent.winfo_rooty()
            pw = parent.winfo_width()
            ph = parent.winfo_height()
            x = px + (pw - w) // 2
            y = py + (ph - h) // 2
        except Exception:
            x = (sw - w) // 2
            y = (sh - h) // 2
    else:
        x = (sw - w) // 2
        y = (sh - h) // 2
    x = max(0, min(x, sw - w))
    y = max(0, min(y, sh - h))
    win.geometry(f"{w}x{h}+{x}+{y}")
    win.update_idletasks()


def safe_show_error(title, message, parent=None):
    """Show error messagebox with parent support"""
    messagebox.showerror(title, message, parent=parent)


def safe_show_info(title, message, parent=None):
    """Show info messagebox with parent support"""
    messagebox.showinfo(title, message, parent=parent)


def safe_show_warning(title, message, parent=None):
    """Show warning messagebox with parent support"""
    messagebox.showwarning(title, message, parent=parent)
