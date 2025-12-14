#!/usr/bin/env python3
"""
Proponowana zakładka konfiguracji poczty - Tkinter
Zawiera:
 - wybór typu konta: Exchange / IMAP/SMTP / POP3/SMTP
 - pola: Nazwa konta, Adres e-mail, Login, Hasło
 - metoda uwierzytelniania: Hasło / OAuth2 / App Password / PLAIN
 - ustawienia Exchange: Serwer Exchange, Domena (opcjonalnie)
 - przyciski: Testuj połączenie, Zapisz ustawienia, Gotowy
Uwagi:
 - Funkcja test_connect() i save_settings() zawierają miejsca (TODO)
   gdzie warto wpiąć istniejący kod z dzieju-app2 (np. logika testu połączenia,
   zapisu konfiguracji, handling OAuth2).
"""
import tkinter as tk
from tkinter import ttk, messagebox
import configparser
import os

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".poczta_faktury_mail_config.ini")


class MailConfigFrame(ttk.Frame):
    def __init__(self, master=None, initial=None, **kwargs):
        super().__init__(master, **kwargs)
        self.initial = initial or {}
        self._create_widgets()
        self._place_widgets()
        self._load_initial()

    def _create_widgets(self):
        # Główna ramka tytułowa
        self.lbl_title = ttk.Label(self, text="Konfiguracja konta", font=("TkDefaultFont", 10, "bold"))

        # Typ konta
        self.account_type_var = tk.StringVar(value="Exchange")
        self.account_type_frame = ttk.LabelFrame(self, text="Typ konta")
        self.rb_exchange = ttk.Radiobutton(self.account_type_frame, text="Exchange", variable=self.account_type_var, value="Exchange", command=self._on_account_type_change)
        self.rb_imap = ttk.Radiobutton(self.account_type_frame, text="IMAP/SMTP", variable=self.account_type_var, value="IMAP")
        self.rb_pop3 = ttk.Radiobutton(self.account_type_frame, text="POP3/SMTP", variable=self.account_type_var, value="POP3")

        # Dane konta
        self.entries_frame = ttk.Frame(self)
        self.account_name_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.login_var = tk.StringVar()
        self.password_var = tk.StringVar()

        self.lbl_account_name = ttk.Label(self.entries_frame, text="Nazwa konta:")
        self.entry_account_name = ttk.Entry(self.entries_frame, textvariable=self.account_name_var, width=40)

        self.lbl_email = ttk.Label(self.entries_frame, text="Adres e-mail:")
        self.entry_email = ttk.Entry(self.entries_frame, textvariable=self.email_var, width=40)

        self.lbl_login = ttk.Label(self.entries_frame, text="Login:")
        self.entry_login = ttk.Entry(self.entries_frame, textvariable=self.login_var, width=40)

        self.lbl_password = ttk.Label(self.entries_frame, text="Hasło:")
        self.entry_password = ttk.Entry(self.entries_frame, textvariable=self.password_var, show="*", width=40)

        # Metoda uwierzytelniania
        self.auth_frame = ttk.LabelFrame(self, text="Metoda uwierzytelniania:")
        self.auth_var = tk.StringVar(value="Haslo")
        self.rb_auth_password = ttk.Radiobutton(self.auth_frame, text="Hasło", variable=self.auth_var, value="Haslo")
        self.rb_auth_oauth2 = ttk.Radiobutton(self.auth_frame, text="OAuth2", variable=self.auth_var, value="OAuth2")
        self.rb_auth_app_password = ttk.Radiobutton(self.auth_frame, text="App Password", variable=self.auth_var, value="AppPassword")
        self.rb_auth_plain = ttk.Radiobutton(self.auth_frame, text="PLAIN/Plain Text", variable=self.auth_var, value="PLAIN")

        # Ustawienia Exchange (pokazywane tylko gdy wybierzesz Exchange)
        self.exchange_frame = ttk.LabelFrame(self, text="Ustawienia Exchange")
        self.exchange_server_var = tk.StringVar()
        self.exchange_domain_var = tk.StringVar()

        self.lbl_exchange_server = ttk.Label(self.exchange_frame, text="Serwer Exchange:")
        self.entry_exchange_server = ttk.Entry(self.exchange_frame, textvariable=self.exchange_server_var, width=40)

        self.lbl_exchange_domain = ttk.Label(self.exchange_frame, text="Domena (opcjonalnie):")
        self.entry_exchange_domain = ttk.Entry(self.exchange_frame, textvariable=self.exchange_domain_var, width=40)

        # Przyciski
        self.buttons_frame = ttk.Frame(self)
        self.btn_test = ttk.Button(self.buttons_frame, text="Testuj połączenie", command=self.test_connection)
        self.btn_save = ttk.Button(self.buttons_frame, text="Zapisz ustawienia", command=self.save_settings)
        self.btn_done = ttk.Button(self.buttons_frame, text="Gotowy", command=self.on_done)

    def _place_widgets(self):
        pad = {"padx": 6, "pady": 4}
        self.lbl_title.grid(row=0, column=0, sticky="w", **pad)

        # account type
        self.account_type_frame.grid(row=1, column=0, sticky="ew", **pad)
        self.rb_exchange.grid(row=0, column=0, padx=6, pady=4, sticky="w")
        self.rb_imap.grid(row=0, column=1, padx=6, pady=4, sticky="w")
        self.rb_pop3.grid(row=0, column=2, padx=6, pady=4, sticky="w")

        # entries
        self.entries_frame.grid(row=2, column=0, sticky="ew", **pad)
        self.lbl_account_name.grid(row=0, column=0, sticky="e")
        self.entry_account_name.grid(row=0, column=1, sticky="w")
        self.lbl_email.grid(row=1, column=0, sticky="e")
        self.entry_email.grid(row=1, column=1, sticky="w")
        self.lbl_login.grid(row=2, column=0, sticky="e")
        self.entry_login.grid(row=2, column=1, sticky="w")
        self.lbl_password.grid(row=3, column=0, sticky="e")
        self.entry_password.grid(row=3, column=1, sticky="w")

        # auth
        self.auth_frame.grid(row=3, column=0, sticky="ew", **{"padx": 6, "pady": 0})
        self.rb_auth_password.grid(row=0, column=0, padx=6, pady=4, sticky="w")
        self.rb_auth_oauth2.grid(row=0, column=1, padx=6, pady=4, sticky="w")
        self.rb_auth_app_password.grid(row=0, column=2, padx=6, pady=4, sticky="w")
        self.rb_auth_plain.grid(row=0, column=3, padx=6, pady=4, sticky="w")

        # exchange
        self.exchange_frame.grid(row=4, column=0, sticky="ew", **pad)
        self.lbl_exchange_server.grid(row=0, column=0, sticky="e")
        self.entry_exchange_server.grid(row=0, column=1, sticky="w")
        self.lbl_exchange_domain.grid(row=1, column=0, sticky="e")
        self.entry_exchange_domain.grid(row=1, column=1, sticky="w")

        # buttons
        self.buttons_frame.grid(row=5, column=0, sticky="e", **pad)
        self.btn_test.grid(row=0, column=0, padx=6)
        self.btn_save.grid(row=0, column=1, padx=6)
        # stylizowany zielony przycisk "Gotowy"
        self.btn_done.grid(row=0, column=2, padx=6)
        self._on_account_type_change()  # ukryj/pokaż sekcje zależne od typu konta

    def _on_account_type_change(self):
        t = self.account_type_var.get()
        if t == "Exchange":
            self.exchange_frame.state(["!disabled"])
            for child in self.exchange_frame.winfo_children():
                child.configure(state="normal")
        else:
            # ukryj lub dezaktywuj pola Exchange
            for child in self.exchange_frame.winfo_children():
                child.configure(state="disabled")

    def _load_initial(self):
        # jeśli dostępne - wczytaj z self.initial lub z pliku konfiguracyjnego
        cfg = configparser.ConfigParser()
        if os.path.exists(CONFIG_FILE):
            try:
                cfg.read(CONFIG_FILE)
                s = cfg["mail"]
                self.account_type_var.set(s.get("type", "Exchange"))
                self.account_name_var.set(s.get("account_name", ""))
                self.email_var.set(s.get("email", ""))
                self.login_var.set(s.get("login", ""))
                self.password_var.set(s.get("password", ""))
                self.auth_var.set(s.get("auth_method", "Haslo"))
                self.exchange_server_var.set(s.get("exchange_server", ""))
                self.exchange_domain_var.set(s.get("exchange_domain", ""))
            except Exception:
                # ignoruj błędy parsowania
                pass
        # nadpisz wartości początkowe jeśli podano
        for k, v in self.initial.items():
            if hasattr(self, f"{k}_var"):
                getattr(self, f"{k}_var").set(v)

    def test_connection(self):
        # Tu powinna być realna implementacja testu połączenia.
        # Możesz wpiąć tutaj funkcje z dzieju-app2 które robią testy Exchange/IMAP/POP3.
        t = self.account_type_var.get()
        auth = self.auth_var.get()
        server = self.exchange_server_var.get() if t == "Exchange" else None
        login = self.login_var.get()
        password = self.password_var.get()
        email = self.email_var.get()

        # Proste sprawdzenie pól
        if not login or not password or not email:
            messagebox.showwarning("Brak danych", "Uzupełnij pola Login, Hasło i Adres e-mail przed testem.")
            return

        # TODO: WSTAW TUTAJ RZECZYWISTY TEST POŁĄCZENIA:
        # - dla Exchange: użyj kodu z dzieju-app2 (np. test_exchange_connection(server, login, password))
        # - dla IMAP/POP3: analogicznie (skorzystaj z istniejącej logiki)
        #
        # Poniżej jest symulacja sukcesu (usuń/przerób).
        try:
            # przykład wywołania (przykładowa funkcja z innego repo):
            # success, msg = test_exchange_connection(server, login, password, auth_method=auth)
            # if success: ...
            success = True
            msg = "Połączenie wykonane pomyślnie (symulacja)."
            if success:
                messagebox.showinfo("Test połączenia", msg)
            else:
                messagebox.showerror("Test połączenia", msg or "Błąd połączenia")
        except Exception as e:
            messagebox.showerror("Test połączenia", f"Błąd podczas testu połączenia:\n{e}")

    def save_settings(self):
        # Zapisz ustawienia do pliku ini (można podmienić na istniejący mechanizm zapisu)
        cfg = configparser.ConfigParser()
        cfg["mail"] = {
            "type": self.account_type_var.get(),
            "account_name": self.account_name_var.get(),
            "email": self.email_var.get(),
            "login": self.login_var.get(),
            "password": self.password_var.get(),
            "auth_method": self.auth_var.get(),
            "exchange_server": self.exchange_server_var.get(),
            "exchange_domain": self.exchange_domain_var.get(),
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                cfg.write(f)
            messagebox.showinfo("Zapis", "Ustawienia zostały zapisane.")
        except Exception as e:
            messagebox.showerror("Zapis", f"Nie udało się zapisać ustawień:\n{e}")

    def on_done(self):
        # Domyślna akcja przy Gotowy - zamknij okno lub schowaj ramkę.
        parent = self.winfo_toplevel()
        try:
            parent.destroy()
        except Exception:
            # jeśli nie chcemy niszczyć najwyższego okna, schowaj ramkę
            self.master.forget()

if __name__ == "__main__":
    # szybk test wizualny
    root = tk.Tk()
    root.title("Konfiguracja konta - demo")
    frame = MailConfigFrame(root, padding=10)
    frame.pack(fill="both", expand=True)
    root.mainloop()
