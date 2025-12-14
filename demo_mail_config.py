"""# demo_mail_config.py - proste uruchomienie okna konfiguracji
import tkinter as tk
from gui.mail_config import MailConfigFrame

if __name__ == '__main__':
    root = tk.Tk()
    root.title('Poczta-Faktury - Konfiguracja konta (demo)')
    frame = MailConfigFrame(root)
    root.geometry('640x360')
    root.mainloop()
"""