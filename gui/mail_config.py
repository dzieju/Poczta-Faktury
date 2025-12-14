"""# GUI zakładka: Konfiguracja konta (Tkinter)
# Dodaj do repo: gui/mail_config.py

import json
import os
import imaplib
import poplib
import tkinter as tk
from tkinter import ttk, messagebox

# opcjonalne importy
try:
    from exchangelib import Account, Credentials, Configuration as ExchConfiguration, DELEGATE
    EXCHANGELIB_AVAILABLE = True
except Exception:
    EXCHANGELIB_AVAILABLE = False

CONFIG_PATH = os.path.expanduser("~/.poczta_faktury_accounts.json")


class MailConfigFrame(ttk.Frame):
    def __init__(self, master=None, **kw):
        super().__init__(master, **kw)
        self.pack(fill="both", expand=True)
        self._build_ui()
        self._load_defaults()

    def _build_ui(self):
        pad = {"padx": 6, "pady": 4}

        # Typ konta
        top = ttk.LabelFrame(self, text="Konfiguracja konta")
        top.pack(fill="x", **pad)

        self.account_type = tk.StringVar(value="Exchange")
        rb_frame = ttk.Frame(top)
        rb_frame.grid(row=0, column=0, sticky="w", **pad)
        ttk.Label(rb_frame, text="Typ konta:").pack(side="left")
        for t in ("Exchange", "IMAP/SMTP", "POP3/SMTP"):
            ttk.Radiobutton(rb_frame, text=t, value=t, variable=self.account_type, command=self._on_type_change).pack(side="left", padx=6)

        # Dane konta
        form = ttk.Frame(top)
        form.grid(row=1, column=0, sticky="w", **pad)

        ttk.Label(form, text="Nazwa konta:").grid(row=0, column=0, sticky="e")
        self.entry_name = ttk.Entry(form, width=40)
        self.entry_name.grid(row=0, column=1, sticky="w")

        ttk.Label(form, text="Adres e-mail:").grid(row=1, column=0, sticky="e")
        self.entry_email = ttk.Entry(form, width=40)
        self.entry_email.grid(row=1, column=1, sticky="w")

        ttk.Label(form, text="Login:").grid(row=2, column=0, sticky="e")
        self.entry_login = ttk.Entry(form, width=40)
        self.entry_login.grid(row=2, column=1, sticky="w")

        ttk.Label(form, text="Has2o:").grid(row=3, column=0, sticky="e")
        self.entry_password = ttk.Entry(form, width=40, show="*")
        self.entry_password.grid(row=3, column=1, sticky="w")

        # Metoda uwierzytelniania
        auth_frame = ttk.Frame(top)
        auth_frame.grid(row=2, column=0, sticky="w", **pad)
        ttk.Label(auth_frame, text="Metoda uwierzytelniania:").pack(side="left")
        self.auth_method = tk.StringVar(value="Haslo")
        for a in ("Haslo", "OAuth2", "App Password", "PLAIN"):
            ttk.Radiobutton(auth_frame, text=a, value=a, variable=self.auth_method).pack(side="left", padx=6)

        # Ustawienia Exchange (pokazywane tylko dla Exchange)
        self.exchange_frame = ttk.LabelFrame(self, text="Ustawienia Exchange")
        self.exchange_frame.pack(fill="x", **pad)

        ttk.Label(self.exchange_frame, text="Serwer Exchange:").grid(row=0, column=0, sticky="e")
        self.entry_exch_server = ttk.Entry(self.exchange_frame, width=40)
        self.entry_exch_server.grid(row=0, column=1, sticky="w")

        ttk.Label(self.exchange_frame, text="Domena (opcjonalnie):").grid(row=1, column=0, sticky="e")
        self.entry_exch_domain = ttk.Entry(self.exchange_frame, width=40)
        self.entry_exch_domain.grid(row=1, column=1, sticky="w")

        # Przyciski
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", **pad)
        ttk.Button(btn_frame, text="Testuj po2%czenie", command=self.on_test).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="Zapisz ustawienia", command=self.on_save).pack(side="left", padx=6)
        self.ready_label = ttk.Label(btn_frame, text="", foreground="green")
        self.ready_label.pack(side="left", padx=12)

        self._on_type_change()

    def _on_type_change(self):
        typ = self.account_type.get()
        if typ == "Exchange":
            self.exchange_frame.pack(fill="x", padx=6, pady=4)
        else:
            self.exchange_frame.forget()

    def _load_defaults(self):
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # jeeli s4 konta, za2aduj pierwsze (przyk2ad)
                    if data and isinstance(data, list):
                        acc = data[0]
                        self.entry_name.insert(0, acc.get("name", ""))
                        self.entry_email.insert(0, acc.get("email", ""))
                        self.entry_login.insert(0, acc.get("login", ""))
                        self.entry_password.insert(0, acc.get("password", ""))
                        self.account_type.set(acc.get("type", "Exchange"))
                        self.auth_method.set(acc.get("auth", "Haslo"))
                        self.entry_exch_server.insert(0, acc.get("exchange_server", ""))
                        self.entry_exch_domain.insert(0, acc.get("exchange_domain", ""))
                        self._on_type_change()
            except Exception:
                pass

    def _gather(self):
        return {
            "name": self.entry_name.get().strip(),
            "email": self.entry_email.get().strip(),
            "login": self.entry_login.get().strip(),
            "password": self.entry_password.get(),
            "type": self.account_type.get(),
            "auth": self.auth_method.get(),
            "exchange_server": self.entry_exch_server.get().strip(),
            "exchange_domain": self.entry_exch_domain.get().strip(),
        }

    def on_save(self):
        cfg = self._gather()
        # proste zapisywanie: lista kont
        accounts = []
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    accounts = json.load(f)
            except Exception:
                accounts = []
        # nadpisz pierwsze lub dodaj
        if accounts:
            accounts[0] = cfg
        else:
            accounts.append(cfg)
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(accounts, f, ensure_ascii=False, indent=2)
        self.ready_label.config(text="Gotowy")
        messagebox.showinfo("Zapisano", "Ustawienia zapisane pomy2nie.\nUwaga: has2a s4 przechowywane w formie niezaszyfrowanej 	6 rozwacenie szyfrowanie.")

    def on_test(self):
        cfg = self._gather()
        typ = cfg["type"]
        try:
            if typ == "IMAP/SMTP":
                self._test_imap(cfg)
            elif typ == "POP3/SMTP":
                self._test_pop3(cfg)
            else:  # Exchange
                self._test_exchange(cfg)
        except Exception as e:
            messagebox.showerror("B2d pocenia", str(e))

    def _test_imap(self, cfg):
        # pr2ba po2czenia IMAP SSL na domy2owym porcie 993
        host = cfg.get("exchange_server") or ""
        if not host:
            host = "imap." + cfg.get("email").split("@")[-1] if cfg.get("email") else ""
        if not host:
            raise RuntimeError("Nie podano serwera IMAP.")
        try:
            imap = imaplib.IMAP4_SSL(host)
            imap.login(cfg["login"], cfg["password"])
            imap.logout()
            messagebox.showinfo("Sukces", "Po2czenie IMAP OK")
        except Exception as e:
            raise RuntimeError(f"B2d IMAP: {e}")

    def _test_pop3(self, cfg):
        host = cfg.get("exchange_server") or ("pop." + cfg.get("email").split("@")[-1] if cfg.get("email") else "")
        if not host:
            raise RuntimeError("Nie podano serwera POP3.")
        try:
            pop = poplib.POP3_SSL(host)
            pop.user(cfg["login"])
            pop.pass_(cfg["password"])
            pop.quit()
            messagebox.showinfo("Sukces", "Po2czenie POP3 OK")
        except Exception as e:
            raise RuntimeError(f"B2d POP3: {e}")

    def _test_exchange(self, cfg):
        if not EXCHANGELIB_AVAILABLE:
            raise RuntimeError("Biblioteka exchangelib nie jest zainstalowana. Zainstaluj exchangelib (pip install exchangelib) i spr2buj ponownie.")
        server = cfg.get("exchange_server") or None
        try:
            creds = Credentials(username=cfg["login"], password=cfg["password"])
            exch_config = ExchConfiguration(server=server) if server else None
            account = Account(primary_smtp_address=cfg.get("email"), credentials=creds, autodiscover=(exch_config is None), config=exch_config, access_type=DELEGATE)
            # proste sprawdzenie: odbwiec root
            account.root.refresh()
            messagebox.showinfo("Sukces", "Po2czenie Exchange OK")
        except Exception as e:
            raise RuntimeError(f"B2d Exchange: {e}")


if __name__ == '__main__':
    root = tk.Tk()
    root.title('Konfiguracja konta - demo')
    MailConfigFrame(root)
    root.mainloop()
"""