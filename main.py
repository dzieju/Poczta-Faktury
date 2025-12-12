#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Główny punkt wejścia aplikacji Poczta-Faktury
"""

import tkinter as tk
from poczta_faktury import EmailInvoiceFinderApp

if __name__ == '__main__':
    root = tk.Tk()
    app = EmailInvoiceFinderApp(root)
    root.mainloop()
