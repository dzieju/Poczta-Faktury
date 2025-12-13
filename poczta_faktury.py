#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplikacja do wyszukiwania faktur w załącznikach email po numerze NIP
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import imaplib
import poplib
import email
from email.header import decode_header
import os
import re
import tempfile
from pathlib import Path
import PyPDF2
import pdfplumber
import json
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
import threading
import queue
import subprocess
import platform

# Plik konfiguracyjny
CONFIG_FILE = Path.home() / '.poczta_faktury_config.json'

# Plik z wersją aplikacji
VERSION_FILE = Path(__file__).parent / 'version.txt'

# Plik z danymi znalezionych faktur
FOUND_INVOICES_FILE = Path.home() / '.poczta_faktury_found.json'


class EmailInvoiceFinderApp:
    """Główna aplikacja do wyszukiwania faktur"""
    
    def __init__(self, root):
        self.root = root
        
        # Wczytaj wersję aplikacji
        self.version = self._load_version()
        
        # Ustaw tytuł okna z wersją
        self._update_window_title()
        
        self.root.geometry("800x600")
        
        # Konfiguracja email
        self.email_config = {
            'protocol': 'IMAP',
            'server': '',
            'port': '',
            'email': '',
            'password': '',
            'use_ssl': True,
            'save_email_settings': False
        }
        
        # Ustawienia wyszukiwania
        self.search_config = {
            'nip': '',
            'output_folder': '',
            'save_search_settings': False,
            'range_1m': False,
            'range_3m': False,
            'range_6m': False,
            'range_week': False,
            'invoice_filename_pattern': r'fakt',  # Domyślny wzorzec dla faktur
            'overwrite_policy': 'suffix',  # 'overwrite' lub 'suffix'
            'search_all_folders': True  # Przeszukuj wszystkie foldery rekursywnie
        }
        
        # Lista znalezionych faktur (przechowuje metadata)
        self.found_invoices = []
        
        # Threading controls for non-blocking search
        self.search_thread = None
        self.stop_event = threading.Event()
        self.log_queue = queue.Queue()
        
        # Wczytaj konfigurację z pliku
        self.load_config()
        
        # Wczytaj znalezione faktury
        self.load_found_invoices()
        
        self.create_widgets()
        
        # Uruchom watcher pliku wersji
        self.root.after(5000, self._watch_version_file)
    
    def create_widgets(self):
        """Tworzenie interfejsu użytkownika"""
        # Notebook (zakładki)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Zakładka 1: Konfiguracja email
        self.config_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.config_frame, text="Konfiguracja poczty")
        self.create_email_config_tab()
        
        # Zakładka 2: Wyszukiwanie NIP (with inner notebook for Wyniki and Znalezione)
        self.search_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.search_frame, text="Wyszukiwanie NIP")
        self.create_search_tab()
        
        # Zakładka 3: Znalezione faktury (history of all found invoices)
        self.found_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.found_frame, text="Znalezione faktury")
        self.create_found_tab()
        
        # Zakładka 4: O programie
        self.about_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.about_frame, text="O programie")
        self.create_about_tab()
        
        # Zastosuj wczytaną konfigurację do UI
        self._apply_loaded_config_to_ui()
    
    def create_email_config_tab(self):
        """Tworzenie zakładki konfiguracji email"""
        # Protokół
        protocol_frame = ttk.LabelFrame(self.config_frame, text="Protokół", padding=10)
        protocol_frame.grid(row=0, column=0, columnspan=2, sticky='ew', padx=10, pady=5)
        
        self.protocol_var = tk.StringVar(value='IMAP')
        ttk.Radiobutton(protocol_frame, text="IMAP", variable=self.protocol_var, 
                       value='IMAP').pack(side='left', padx=5)
        ttk.Radiobutton(protocol_frame, text="POP3", variable=self.protocol_var, 
                       value='POP3').pack(side='left', padx=5)
        ttk.Radiobutton(protocol_frame, text="Exchange (IMAP)", variable=self.protocol_var, 
                       value='EXCHANGE').pack(side='left', padx=5)
        
        # Serwer
        ttk.Label(self.config_frame, text="Serwer:").grid(row=1, column=0, sticky='w', padx=10, pady=5)
        self.server_entry = ttk.Entry(self.config_frame, width=40)
        self.server_entry.grid(row=1, column=1, sticky='ew', padx=10, pady=5)
        
        # Port
        ttk.Label(self.config_frame, text="Port:").grid(row=2, column=0, sticky='w', padx=10, pady=5)
        self.port_entry = ttk.Entry(self.config_frame, width=40)
        self.port_entry.grid(row=2, column=1, sticky='ew', padx=10, pady=5)
        self.port_entry.insert(0, "993")  # Domyślny port IMAP SSL
        
        # Email
        ttk.Label(self.config_frame, text="Email:").grid(row=3, column=0, sticky='w', padx=10, pady=5)
        self.email_entry = ttk.Entry(self.config_frame, width=40)
        self.email_entry.grid(row=3, column=1, sticky='ew', padx=10, pady=5)
        
        # Hasło
        ttk.Label(self.config_frame, text="Hasło:").grid(row=4, column=0, sticky='w', padx=10, pady=5)
        self.password_entry = ttk.Entry(self.config_frame, width=40, show='*')
        self.password_entry.grid(row=4, column=1, sticky='ew', padx=10, pady=5)
        
        # Pokaż hasło
        self.show_password_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self.config_frame, text="Pokaż hasło", 
                       variable=self.show_password_var,
                       command=self.toggle_show_password).grid(row=5, column=0, columnspan=2, padx=10, pady=5)
        
        # SSL
        self.ssl_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.config_frame, text="Użyj SSL/TLS", 
                       variable=self.ssl_var).grid(row=6, column=0, columnspan=2, padx=10, pady=5)
        
        # Zapisz ustawienia
        self.save_email_config_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self.config_frame, text="Zapisz ustawienia", 
                       variable=self.save_email_config_var).grid(row=7, column=0, columnspan=2, padx=10, pady=5)
        
        # Przycisk testowania połączenia
        ttk.Button(self.config_frame, text="Testuj połączenie", 
                  command=self.test_connection).grid(row=8, column=0, columnspan=2, pady=20)
        
        # Status
        self.status_label = ttk.Label(self.config_frame, text="", foreground="blue")
        self.status_label.grid(row=9, column=0, columnspan=2, padx=10, pady=5)
        
        self.config_frame.columnconfigure(1, weight=1)
    
    def create_search_tab(self):
        """Tworzenie zakładki wyszukiwania z wewnętrznym notebookiem"""
        # Top section with search inputs
        input_frame = ttk.Frame(self.search_frame)
        input_frame.pack(fill='x', padx=10, pady=10)
        
        # NIP
        ttk.Label(input_frame, text="Numer NIP:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.nip_entry = ttk.Entry(input_frame, width=40)
        self.nip_entry.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        
        # Folder wyjściowy
        ttk.Label(input_frame, text="Folder zapisu:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        
        folder_frame = ttk.Frame(input_frame)
        folder_frame.grid(row=1, column=1, sticky='ew', padx=5, pady=5)
        
        self.folder_entry = ttk.Entry(folder_frame, width=30)
        self.folder_entry.pack(side='left', fill='x', expand=True)
        
        ttk.Button(folder_frame, text="Przeglądaj...", 
                  command=self.browse_folder).pack(side='left', padx=5)
        
        # Zakres czasowy
        range_frame = ttk.LabelFrame(input_frame, text="Zakres przeszukiwania", padding=10)
        range_frame.grid(row=2, column=0, columnspan=2, sticky='ew', padx=5, pady=5)
        
        self.range_1m_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(range_frame, text="1 miesiąc", 
                       variable=self.range_1m_var).pack(side='left', padx=5)
        
        self.range_3m_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(range_frame, text="3 miesiące", 
                       variable=self.range_3m_var).pack(side='left', padx=5)
        
        self.range_6m_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(range_frame, text="6 miesięcy", 
                       variable=self.range_6m_var).pack(side='left', padx=5)
        
        self.range_week_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(range_frame, text="Ostatni tydzień", 
                       variable=self.range_week_var).pack(side='left', padx=5)
        
        # Zapisz ustawienia
        self.save_search_config_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(input_frame, text="Zapisz ustawienia", 
                       variable=self.save_search_config_var).grid(row=3, column=0, columnspan=2, padx=5, pady=5)
        
        # Przyciski wyszukiwania
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        self.search_button = ttk.Button(button_frame, text="Szukaj faktur", 
                   command=self.start_search_thread)
        self.search_button.pack(side='left', padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="Przerwij", 
                   command=self.stop_search, state='disabled')
        self.stop_button.pack(side='left', padx=5)
        
        # Pasek postępu
        self.progress = ttk.Progressbar(input_frame, mode='indeterminate')
        self.progress.grid(row=5, column=0, columnspan=2, sticky='ew', padx=5, pady=5)
        
        input_frame.columnconfigure(1, weight=1)
        
        # Inner notebook for Wyniki and Znalezione tabs
        self.search_inner_notebook = ttk.Notebook(self.search_frame)
        self.search_inner_notebook.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Tab 1: Wyniki (logs/progress)
        self.results_frame = ttk.Frame(self.search_inner_notebook)
        self.search_inner_notebook.add(self.results_frame, text="Wyniki")
        
        self.results_text = scrolledtext.ScrolledText(self.results_frame, height=15, width=70)
        self.results_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Tab 2: Znalezione (live list of found files)
        self.found_live_frame = ttk.Frame(self.search_inner_notebook)
        self.search_inner_notebook.add(self.found_live_frame, text="Znalezione")
        
        self.found_live_listbox = tk.Listbox(self.found_live_frame)
        scrollbar = ttk.Scrollbar(self.found_live_frame, orient='vertical', command=self.found_live_listbox.yview)
        self.found_live_listbox.configure(yscrollcommand=scrollbar.set)
        self.found_live_listbox.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y', pady=5)
    
    def create_found_tab(self):
        """Tworzenie zakładki Znalezione faktury"""
        # Ramka dla przycisków
        button_frame = ttk.Frame(self.found_frame)
        button_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Button(button_frame, text="Odśwież", 
                  command=self.refresh_found_invoices).pack(side='left', padx=5)
        
        ttk.Button(button_frame, text="Wyczyść wszystko", 
                  command=self.clear_found_invoices).pack(side='left', padx=5)
        
        # Ramka dla tabeli
        table_frame = ttk.Frame(self.found_frame)
        table_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Treeview z kolumnami
        columns = ('date', 'sender', 'subject', 'filename')
        self.found_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=20)
        
        # Definiowanie nagłówków
        self.found_tree.heading('date', text='Data', command=lambda: self.sort_found_column('date', False))
        self.found_tree.heading('sender', text='Nadawca', command=lambda: self.sort_found_column('sender', False))
        self.found_tree.heading('subject', text='Temat', command=lambda: self.sort_found_column('subject', False))
        self.found_tree.heading('filename', text='Nazwa Pliku', command=lambda: self.sort_found_column('filename', False))
        
        # Ustawienie szerokości kolumn
        self.found_tree.column('date', width=150)
        self.found_tree.column('sender', width=200)
        self.found_tree.column('subject', width=250)
        self.found_tree.column('filename', width=200)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.found_tree.yview)
        self.found_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pakowanie
        self.found_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Podwójne kliknięcie otwiera plik
        self.found_tree.bind('<Double-1>', self.on_found_invoice_double_click)
        
        # Załaduj dane do tabeli - pokazuje persisted invoices from FOUND_INVOICES_FILE
        # This ensures that data saved from previous sessions is visible on app startup
        self.root.after(0, self.refresh_found_invoices)
    
    def create_about_tab(self):
        """Tworzenie zakładki O programie"""
        # Ramka centralna
        main_frame = ttk.Frame(self.about_frame)
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)
        
        # Tytuł
        title_label = ttk.Label(main_frame, text="Poczta Faktury", font=('Arial', 20, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # Wersja
        version_label = ttk.Label(main_frame, text=f"Wersja: {self.version}", font=('Arial', 12))
        version_label.pack(pady=(0, 20))
        
        # Separator
        ttk.Separator(main_frame, orient='horizontal').pack(fill='x', pady=10)
        
        # Informacje kontaktowe
        contact_frame = ttk.LabelFrame(main_frame, text="Kontakt", padding=20)
        contact_frame.pack(fill='both', expand=True, pady=10)
        
        contact_info = [
            ("Autor:", "Grzegorz Ciekot"),
            ("Telefon:", "512 623 706  lub  34 363 2868"),
            ("E-mail:", "grzegorz.ciekot@woox.pl"),
            ("Strona:", "woox.pl")
        ]
        
        for i, (label, value) in enumerate(contact_info):
            label_widget = ttk.Label(contact_frame, text=label, font=('Arial', 10, 'bold'))
            label_widget.grid(row=i, column=0, sticky='w', pady=5, padx=(0, 10))
            
            value_widget = ttk.Label(contact_frame, text=value, font=('Arial', 10))
            value_widget.grid(row=i, column=1, sticky='w', pady=5)
        
        # Opis
        ttk.Separator(main_frame, orient='horizontal').pack(fill='x', pady=10)
        
        desc_label = ttk.Label(main_frame, 
                               text="Aplikacja do wyszukiwania faktur\nw załącznikach email po numerze NIP",
                               font=('Arial', 10),
                               justify='center')
        desc_label.pack(pady=10)
    
    def _load_version(self):
        """Wczytywanie wersji aplikacji z pliku version.txt"""
        try:
            if VERSION_FILE.exists():
                version = VERSION_FILE.read_text().strip()
                # Sprawdź czy wersja ma poprawny format (x.y.z)
                import re
                if re.match(r'^\d+\.\d+\.\d+$', version):
                    return version
        except Exception:
            pass
        return "1.0.0"
    
    def _update_window_title(self):
        """Aktualizacja tytułu okna z numerem wersji"""
        self.root.title(f"Poczta Faktury - Wyszukiwanie faktur po NIP  ver. {self.version}")
    
    def _watch_version_file(self):
        """Monitorowanie zmian w pliku version.txt i aktualizacja tytułu"""
        new_version = self._load_version()
        if new_version != self.version:
            self.version = new_version
            self._update_window_title()
        
        # Zaplanuj kolejne sprawdzenie za 5 sekund
        self.root.after(5000, self._watch_version_file)
    
    def toggle_show_password(self):
        """Przełączanie widoczności hasła"""
        if self.show_password_var.get():
            self.password_entry.config(show='')
        else:
            self.password_entry.config(show='*')
    
    def save_config(self):
        """Zapisywanie konfiguracji do pliku JSON"""
        config = {
            'email_config': {
                'protocol': self.protocol_var.get(),
                'server': self.server_entry.get(),
                'port': self.port_entry.get(),
                'email': self.email_entry.get(),
                'password': self.password_entry.get() if self.save_email_config_var.get() else '',
                'use_ssl': self.ssl_var.get(),
                'save_email_settings': self.save_email_config_var.get()
            },
            'search_config': {
                'nip': self.nip_entry.get() if self.save_search_config_var.get() else '',
                'output_folder': self.folder_entry.get() if self.save_search_config_var.get() else '',
                'save_search_settings': self.save_search_config_var.get(),
                'range_1m': self.range_1m_var.get() if self.save_search_config_var.get() else False,
                'range_3m': self.range_3m_var.get() if self.save_search_config_var.get() else False,
                'range_6m': self.range_6m_var.get() if self.save_search_config_var.get() else False,
                'range_week': self.range_week_var.get() if self.save_search_config_var.get() else False,
                'invoice_filename_pattern': self.search_config.get('invoice_filename_pattern', r'fakt'),
                'overwrite_policy': self.search_config.get('overwrite_policy', 'suffix'),
                'search_all_folders': self.search_config.get('search_all_folders', True)
            }
        }
        
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Błąd zapisu konfiguracji: {e}")
            messagebox.showwarning("Ostrzeżenie", f"Nie udało się zapisać konfiguracji:\n{str(e)}")
    
    def load_config(self):
        """Wczytywanie konfiguracji z pliku JSON"""
        if not CONFIG_FILE.exists():
            return
        
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Wczytaj konfigurację email
            email_cfg = config.get('email_config', {})
            self.email_config.update(email_cfg)
            
            # Wczytaj konfigurację wyszukiwania
            search_cfg = config.get('search_config', {})
            self.search_config.update(search_cfg)
            
        except Exception as e:
            print(f"Błąd wczytywania konfiguracji: {e}")
            # Nie pokazujemy błędu przy starcie, żeby nie przeszkadzać użytkownikowi
    
    def _apply_loaded_config_to_ui(self):
        """Zastosowanie wczytanej konfiguracji do UI (wywoływane po utworzeniu widgetów)"""
        # Konfiguracja email
        if self.email_config.get('protocol'):
            self.protocol_var.set(self.email_config['protocol'])
        if self.email_config.get('server'):
            self.server_entry.delete(0, tk.END)
            self.server_entry.insert(0, self.email_config['server'])
        if self.email_config.get('port'):
            self.port_entry.delete(0, tk.END)
            self.port_entry.insert(0, self.email_config['port'])
        if self.email_config.get('email'):
            self.email_entry.delete(0, tk.END)
            self.email_entry.insert(0, self.email_config['email'])
        if self.email_config.get('password'):
            self.password_entry.delete(0, tk.END)
            self.password_entry.insert(0, self.email_config['password'])
        if 'use_ssl' in self.email_config:
            self.ssl_var.set(self.email_config['use_ssl'])
        if 'save_email_settings' in self.email_config:
            self.save_email_config_var.set(self.email_config['save_email_settings'])
        
        # Konfiguracja wyszukiwania
        if self.search_config.get('nip'):
            self.nip_entry.delete(0, tk.END)
            self.nip_entry.insert(0, self.search_config['nip'])
        if self.search_config.get('output_folder'):
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, self.search_config['output_folder'])
        if 'save_search_settings' in self.search_config:
            self.save_search_config_var.set(self.search_config['save_search_settings'])
        if 'range_1m' in self.search_config:
            self.range_1m_var.set(self.search_config['range_1m'])
        if 'range_3m' in self.search_config:
            self.range_3m_var.set(self.search_config['range_3m'])
        if 'range_6m' in self.search_config:
            self.range_6m_var.set(self.search_config['range_6m'])
        if 'range_week' in self.search_config:
            self.range_week_var.set(self.search_config['range_week'])
    
    def test_connection(self):
        """Testowanie połączenia z serwerem email"""
        protocol = self.protocol_var.get()
        server = self.server_entry.get()
        port = self.port_entry.get()
        email_addr = self.email_entry.get()
        password = self.password_entry.get()
        use_ssl = self.ssl_var.get()
        
        if not all([server, port, email_addr, password]):
            messagebox.showerror("Błąd", "Proszę wypełnić wszystkie pola")
            return
        
        try:
            port = int(port)
        except ValueError:
            messagebox.showerror("Błąd", "Port musi być liczbą")
            return
        
        self.status_label.config(text="Łączenie...", foreground="blue")
        self.root.update()
        
        try:
            if protocol == 'POP3':
                if use_ssl:
                    mail = poplib.POP3_SSL(server, port)
                else:
                    mail = poplib.POP3(server, port)
                mail.user(email_addr)
                mail.pass_(password)
                mail.quit()
            else:  # IMAP lub EXCHANGE
                if use_ssl:
                    mail = imaplib.IMAP4_SSL(server, port)
                else:
                    mail = imaplib.IMAP4(server, port)
                mail.login(email_addr, password)
                mail.logout()
            
            self.status_label.config(text="Połączenie udane!", foreground="green")
            messagebox.showinfo("Sukces", "Połączenie z serwerem poczty powiodło się!")
            
            # Zapisz konfigurację
            self.email_config = {
                'protocol': protocol,
                'server': server,
                'port': port,
                'email': email_addr,
                'password': password,
                'use_ssl': use_ssl,
                'save_email_settings': self.save_email_config_var.get()
            }
            
            # Zapisz do pliku jeśli zaznaczono checkbox
            if self.save_email_config_var.get():
                self.save_config()
            
        except Exception as e:
            self.status_label.config(text="Błąd połączenia", foreground="red")
            messagebox.showerror("Błąd", f"Nie udało się połączyć z serwerem:\n{str(e)}")
    
    def browse_folder(self):
        """Wybór folderu do zapisu"""
        folder = filedialog.askdirectory()
        if folder:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder)
    
    def load_found_invoices(self):
        """Wczytywanie listy znalezionych faktur z pliku
        
        Validates that the loaded data is a list and handles JSON corruption gracefully.
        """
        if not FOUND_INVOICES_FILE.exists():
            self.found_invoices = []
            return
        
        try:
            with open(FOUND_INVOICES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Validate that data is a list
            if not isinstance(data, list):
                print(f"Błąd: {FOUND_INVOICES_FILE} zawiera nieprawidłowe dane (nie jest listą). Resetuję dane.")
                self.found_invoices = []
                return
            
            self.found_invoices = data
            print(f"Wczytano {len(self.found_invoices)} znalezionych faktur z pliku")
            
        except json.JSONDecodeError as e:
            print(f"Błąd parsowania JSON z {FOUND_INVOICES_FILE}: {e}. Resetuję dane.")
            self.found_invoices = []
        except Exception as e:
            print(f"Błąd wczytywania znalezionych faktur z {FOUND_INVOICES_FILE}: {e}")
            self.found_invoices = []
    
    def save_found_invoices(self):
        """Zapisywanie listy znalezionych faktur do pliku
        
        Uses atomic write (temp file + os.replace) to prevent corruption if write is interrupted.
        """
        try:
            # Write to temporary file first (atomic write pattern)
            tmp_file = FOUND_INVOICES_FILE.with_suffix('.tmp')
            with open(tmp_file, 'w', encoding='utf-8') as f:
                json.dump(self.found_invoices, f, indent=2, ensure_ascii=False)
            
            # Atomically replace the old file with the new one
            os.replace(tmp_file, FOUND_INVOICES_FILE)
            
        except Exception as e:
            print(f"Błąd zapisu znalezionych faktur do {FOUND_INVOICES_FILE}: {e}")
            # Try to clean up temp file if it exists
            try:
                tmp_file = FOUND_INVOICES_FILE.with_suffix('.tmp')
                if tmp_file.exists():
                    tmp_file.unlink()
            except (OSError, FileNotFoundError):
                pass
    
    def add_found_invoice(self, date, sender, subject, filename, file_path):
        """Dodawanie nowej faktury do listy znalezionych
        
        Ensures self.found_invoices is initialized, appends the invoice with timestamp,
        saves immediately, and logs the operation for debugging.
        """
        # Ensure found_invoices is initialized (defensive programming)
        if not hasattr(self, 'found_invoices') or self.found_invoices is None:
            self.found_invoices = []
        
        invoice = {
            'date': date,
            'sender': sender,
            'subject': subject,
            'filename': filename,
            'file_path': file_path,
            'found_timestamp': datetime.now().isoformat()
        }
        self.found_invoices.append(invoice)
        self.save_found_invoices()
        
        # Log the addition for debugging
        self.safe_log(f"Dodano fakturę do listy: {filename}")
    
    def refresh_found_invoices(self):
        """Odświeżanie tabeli znalezionych faktur
        
        Handles the case when self.found_tree widget doesn't exist yet by scheduling a retry.
        Wraps per-row insertion in try/except to avoid one bad invoice preventing others from showing.
        Logs errors for debugging.
        """
        # Check if the widget exists yet (may be called before create_found_tab completes)
        if not hasattr(self, 'found_tree'):
            # Widget not yet created - schedule a retry
            print("refresh_found_invoices wywoływane za wcześnie - zaplanowano ponowienie")
            self.root.after(100, self.refresh_found_invoices)
            return
        
        try:
            # Wyczyść tabelę
            for item in self.found_tree.get_children():
                self.found_tree.delete(item)
            
            # Dodaj faktury do tabeli (store file_path in tags for efficient access)
            for invoice in self.found_invoices:
                try:
                    self.found_tree.insert('', 'end', values=(
                        invoice.get('date', ''),
                        invoice.get('sender', ''),
                        invoice.get('subject', ''),
                        invoice.get('filename', '')
                    ), tags=(invoice.get('file_path', ''),))
                except Exception as e:
                    # Log error but continue with other invoices
                    print(f"Błąd podczas dodawania faktury do tabeli: {invoice.get('filename', 'unknown')}: {e}")
            
            print(f"Odświeżono tabelę faktur: {len(self.found_invoices)} pozycji")
            
        except Exception as e:
            print(f"Błąd podczas odświeżania tabeli znalezionych faktur: {e}")
    
    def sort_found_column(self, col, reverse):
        """Sortowanie kolumny w tabeli znalezionych faktur"""
        col_index = {'date': 0, 'sender': 1, 'subject': 2, 'filename': 3}
        
        # Pobierz wszystkie elementy
        items = [(self.found_tree.set(k, col), k) for k in self.found_tree.get_children('')]
        
        # Sortuj
        items.sort(reverse=reverse)
        
        # Przeorganizuj elementy
        for index, (val, k) in enumerate(items):
            self.found_tree.move(k, '', index)
        
        # Odwróć kolejność sortowania przy następnym kliknięciu
        self.found_tree.heading(col, command=lambda: self.sort_found_column(col, not reverse))
    
    def clear_found_invoices(self):
        """Czyszczenie listy znalezionych faktur"""
        if messagebox.askyesno("Potwierdzenie", "Czy na pewno chcesz wyczyścić listę znalezionych faktur?"):
            self.found_invoices = []
            self.save_found_invoices()
            self.refresh_found_invoices()
    
    def on_found_invoice_double_click(self, event):
        """Obsługa podwójnego kliknięcia na fakturę - otwiera plik PDF"""
        selection = self.found_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = self.found_tree.item(item, 'values')
        tags = self.found_tree.item(item, 'tags')
        
        if not values or len(values) < 4:
            return
        
        # Pobierz ścieżkę z tagów (jeśli dostępna)
        file_path = tags[0] if tags else None
        
        # Fallback: znajdź po nazwie pliku
        if not file_path:
            filename = values[3]
            for inv in self.found_invoices:
                if inv.get('filename') == filename:
                    file_path = inv.get('file_path', '')
                    break
        
        if not file_path:
            messagebox.showerror("Błąd", "Nie znaleziono ścieżki do pliku")
            return
        
        if not os.path.exists(file_path):
            # Plik nie istnieje
            response = messagebox.askyesnocancel(
                "Plik nie istnieje",
                f"Plik {os.path.basename(file_path)} nie został znaleziony.\n\n"
                f"Oczekiwana ścieżka: {file_path}\n\n"
                "Czy chcesz otworzyć folder nadrzędny?"
            )
            
            if response:  # Yes - otwórz folder
                folder_path = os.path.dirname(file_path) if file_path else os.path.expanduser('~')
                if os.path.exists(folder_path):
                    self.open_file(folder_path)
                else:
                    messagebox.showerror("Błąd", f"Folder również nie istnieje: {folder_path}")
        else:
            # Plik istnieje - otwórz go
            self.open_file(file_path)
    
    def open_file(self, file_path):
        """Otwieranie pliku za pomocą domyślnej aplikacji systemowej (cross-platform)"""
        try:
            system = platform.system()
            
            if system == 'Windows':
                os.startfile(file_path)
            elif system == 'Darwin':  # macOS
                subprocess.run(['open', file_path], check=True)
            else:  # Linux i inne
                subprocess.run(['xdg-open', file_path], check=True)
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można otworzyć pliku:\n{str(e)}")
    
    
    def safe_log(self, message):
        """Thread-safe logging to queue"""
        self.log_queue.put({'type': 'log', 'message': message})
    
    def _poll_log_queue(self):
        """Poll result queue and update GUI - called periodically via root.after
        
        Handles both log messages and found file notifications.
        """
        try:
            while True:
                item = self.log_queue.get_nowait()
                
                if item.get('type') == 'log':
                    # Log message - add to results text
                    message = item.get('message', '')
                    self.results_text.insert(tk.END, message + "\n")
                    self.results_text.see(tk.END)
                    self.root.update_idletasks()
                    
                elif item.get('type') == 'found':
                    # Found file - add to live listbox
                    path = item.get('path') or item.get('name') or str(item)
                    self.found_live_listbox.insert('end', path)
                    self.found_live_listbox.see('end')
                    self.root.update_idletasks()
                    
        except queue.Empty:
            pass
        
        # Schedule next poll if search is running
        if self.search_thread and self.search_thread.is_alive():
            self.root.after(200, self._poll_log_queue)  # 200ms polling interval
    
    def start_search_thread(self):
        """Start search in a separate thread"""
        # Validate inputs
        nip = self.nip_entry.get().strip()
        output_folder = self.folder_entry.get().strip()
        
        if not nip:
            messagebox.showerror("Błąd", "Proszę podać numer NIP")
            return
        
        if not output_folder:
            messagebox.showerror("Błąd", "Proszę wybrać folder zapisu")
            return
        
        if not os.path.exists(output_folder):
            messagebox.showerror("Błąd", "Wybrany folder nie istnieje")
            return
        
        if not self.email_config.get('server'):
            messagebox.showerror("Błąd", "Proszę najpierw skonfigurować połączenie email")
            self.notebook.select(0)  # Przełącz na zakładkę konfiguracji
            return
        
        # Update search_config
        self.search_config = {
            'nip': nip,
            'output_folder': output_folder,
            'save_search_settings': self.save_search_config_var.get(),
            'range_1m': self.range_1m_var.get(),
            'range_3m': self.range_3m_var.get(),
            'range_6m': self.range_6m_var.get(),
            'range_week': self.range_week_var.get()
        }
        
        # Save config if checkbox is checked
        if self.save_search_config_var.get():
            self.save_config()
        
        # Clear results and prepare UI
        self.results_text.delete(1.0, tk.END)
        self.found_live_listbox.delete(0, tk.END)  # Clear live found list
        self.stop_event.clear()
        
        # Update button states
        self.search_button.config(state='disabled')
        self.stop_button.config(state='normal')
        
        # Start progress bar
        self.progress.start()
        
        # Prepare search parameters
        params = {
            'nip': nip,
            'output_folder': output_folder,
            'protocol': self.email_config['protocol'],
            'cutoff_dt': self._get_cutoff_datetime()
        }
        
        # Start search thread
        self.search_thread = threading.Thread(target=self._search_worker, args=(params,), daemon=True)
        self.search_thread.start()
        
        # Start polling log queue
        self.root.after(100, self._poll_log_queue)
    
    def stop_search(self):
        """Stop the running search"""
        self.stop_event.set()
        self.safe_log("Przerwano przez użytkownika - czekam na zakończenie...")
        self.stop_button.config(state='disabled')
    
    def _restore_ui_after_search(self):
        """Restore UI state after search completes - called from worker thread via root.after"""
        self.progress.stop()
        self.search_button.config(state='normal')
        self.stop_button.config(state='disabled')
    
    def _get_email_timestamp(self, email_message):
        """Extract timestamp from email Date header, return epoch time or None"""
        try:
            date_header = email_message.get('Date')
            if date_header:
                email_dt = parsedate_to_datetime(date_header)
                # Convert to epoch timestamp
                return email_dt.timestamp()
        except (TypeError, ValueError, AttributeError) as e:
            pass
        return None
    
    def _set_file_timestamp(self, file_path, timestamp):
        """Set file mtime and atime to given timestamp"""
        if timestamp:
            try:
                os.utime(file_path, (timestamp, timestamp))
            except (OSError, PermissionError) as e:
                # Log warning but don't fail - timestamp setting is not critical
                # Some filesystems or permissions may prevent timestamp modification
                self.safe_log(f"Ostrzeżenie: Nie można ustawić timestampu dla {os.path.basename(file_path)}")
    
    def _save_attachment_with_timestamp(self, attachment_data, output_path, email_message):
        """Save attachment and set its timestamp from email date"""
        with open(output_path, 'wb') as f:
            f.write(attachment_data)
        
        # Set file timestamp from email date
        timestamp = self._get_email_timestamp(email_message)
        if timestamp:
            self._set_file_timestamp(output_path, timestamp)
    
    def _search_worker(self, params):
        """Worker thread for searching emails - runs in background"""
        try:
            nip = params['nip']
            output_folder = params['output_folder']
            protocol = params['protocol']
            cutoff_dt = params['cutoff_dt']
            
            self.safe_log("Rozpoczynam wyszukiwanie...")
            
            # Information about time range
            if cutoff_dt:
                self.safe_log(f"Filtrowanie wiadomości starszych niż: {cutoff_dt.strftime('%Y-%m-%d')}")
            
            found_count = 0
            
            # Connect to email server
            if protocol == 'POP3':
                found_count = self._search_with_pop3_threaded(nip, output_folder, cutoff_dt)
            else:  # IMAP or EXCHANGE
                found_count = self._search_with_imap_threaded(nip, output_folder, cutoff_dt)
            
            # Log completion
            if self.stop_event.is_set():
                self.safe_log("\n=== Wyszukiwanie przerwane ===")
                self.safe_log(f"Znaleziono faktur przed przerwaniem: {found_count}")
            else:
                self.safe_log("\n=== Zakończono wyszukiwanie ===")
                self.safe_log(f"Znaleziono faktur z NIP {nip}: {found_count}")
                
                # Show message box from main thread
                if found_count > 0:
                    self.root.after(0, lambda: messagebox.showinfo("Sukces", 
                        f"Znaleziono {found_count} faktur(y) z podanym NIP.\nPliki zapisano w: {output_folder}"))
                else:
                    self.root.after(0, lambda: messagebox.showinfo("Informacja", 
                        "Nie znaleziono faktur z podanym NIP"))
        
        except Exception as e:
            self.safe_log(f"\nBŁĄD: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror("Błąd", 
                f"Wystąpił błąd podczas wyszukiwania:\n{str(e)}"))
        
        finally:
            # Restore UI state from main thread
            self.root.after(0, self._restore_ui_after_search)
    
    def _get_cutoff_datetime(self):
        """Obliczanie daty granicznej na podstawie zaznaczonych zakresów
        
        Uwaga: Jeśli zaznaczono wiele zakresów, używany jest najdłuższy (6m > 3m > 1m > 1w).
        """
        # Znajdź najdalszy zaznaczony zakres
        max_days = 0
        if self.range_6m_var.get():
            max_days = 180  # 6 miesięcy ≈ 180 dni
        elif self.range_3m_var.get():
            max_days = 90   # 3 miesiące ≈ 90 dni
        elif self.range_1m_var.get():
            max_days = 30   # 1 miesiąc ≈ 30 dni
        elif self.range_week_var.get():
            max_days = 7    # 1 tydzień = 7 dni
        
        if max_days > 0:
            cutoff_dt = datetime.now() - timedelta(days=max_days)
            return cutoff_dt
        return None
    
    def _email_date_is_within_cutoff(self, date_header, cutoff_dt):
        """Sprawdza czy data wiadomości mieści się w zakresie"""
        if cutoff_dt is None:
            return True  # Brak filtrowania
        
        if not date_header:
            return True  # Brak daty - nie odrzucamy
        
        try:
            email_dt = parsedate_to_datetime(date_header)
            # Jeśli email_dt ma timezone, usuń go dla porównania
            if email_dt.tzinfo is not None:
                email_dt = email_dt.replace(tzinfo=None)
            return email_dt >= cutoff_dt
        except (TypeError, ValueError):
            return True  # W razie błędu parsowania, nie odrzucamy
    
    def list_all_folders_recursively(self, mail):
        """Rekursywnie listuje wszystkie foldery IMAP"""
        try:
            status, folders = mail.list()
            if status != 'OK':
                return ['INBOX']
            
            folder_list = []
            for folder in folders:
                # Parse folder name from IMAP response
                # Format: (\\HasNoChildren) "/" "INBOX"
                folder_str = folder.decode() if isinstance(folder, bytes) else folder
                parts = folder_str.split('"')
                
                if len(parts) >= 3:
                    folder_name = parts[-2]
                    folder_list.append(folder_name)
            
            return folder_list if folder_list else ['INBOX']
        except Exception as e:
            self.safe_log(f"Błąd listowania folderów: {e}")
            return ['INBOX']
    
    def matches_invoice_pattern(self, filename):
        """Sprawdza czy nazwa pliku pasuje do wzorca faktury"""
        if not filename:
            return False
        
        # Pobierz wzorzec z konfiguracji
        pattern = self.search_config.get('invoice_filename_pattern', r'fakt')
        
        try:
            # Sprawdź czy wzorzec występuje w nazwie pliku (bez rozróżniania wielkości liter)
            return re.search(pattern, filename, re.IGNORECASE) is not None
        except re.error:
            # Jeśli regex jest nieprawidłowy, użyj prostego wyszukiwania
            return pattern.lower() in filename.lower()
    
    def get_unique_filename(self, output_folder, filename):
        """Generuje unikalną nazwę pliku zgodnie z polityką nadpisywania"""
        overwrite_policy = self.search_config.get('overwrite_policy', 'suffix')
        output_path = os.path.join(output_folder, filename)
        
        if overwrite_policy == 'overwrite':
            return output_path
        
        # Polityka 'suffix' - dodaj numer jeśli plik istnieje
        if not os.path.exists(output_path):
            return output_path
        
        base, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(os.path.join(output_folder, f"{base}_{counter}{ext}")):
            counter += 1
        
        return os.path.join(output_folder, f"{base}_{counter}{ext}")
    
    def _search_with_imap_threaded(self, nip, output_folder, cutoff_dt):
        """Threaded IMAP search with stop event checking and timestamp setting"""
        found_count = 0
        
        # Connect to server
        if self.email_config['use_ssl']:
            mail = imaplib.IMAP4_SSL(self.email_config['server'], int(self.email_config['port']))
        else:
            mail = imaplib.IMAP4(self.email_config['server'], int(self.email_config['port']))
        
        mail.login(self.email_config['email'], self.email_config['password'])
        
        self.safe_log("Połączono z serwerem IMAP")
        
        # Get list of all folders if configured to search all
        search_all_folders = self.search_config.get('search_all_folders', True)
        
        if search_all_folders:
            folders = self.list_all_folders_recursively(mail)
            self.safe_log(f"Znaleziono {len(folders)} folderów do przeszukania")
        else:
            folders = ['INBOX']
        
        # Search each folder
        for folder in folders:
            if self.stop_event.is_set():
                break
            
            try:
                self.safe_log(f"Przeszukiwanie folderu: {folder}")
                
                # Select folder
                status, _ = mail.select(folder, readonly=True)
                if status != 'OK':
                    self.safe_log(f"  Nie można otworzyć folderu {folder}")
                    continue
                
                # Search all messages in this folder
                status, messages = mail.search(None, 'ALL')
                
                if status != 'OK':
                    self.safe_log(f"  Nie można pobrać listy wiadomości z {folder}")
                    continue
                
                message_ids = messages[0].split()
                total_messages = len(message_ids)
                
                self.safe_log(f"  Folder {folder}: {total_messages} wiadomości")
                
                # Process messages with stop event checking
                for i, msg_id in enumerate(message_ids, 1):
                    # Check if stop was requested
                    if self.stop_event.is_set():
                        break
                    
                    if i % 10 == 0:
                        self.safe_log(f"  {folder}: Przetworzono {i}/{total_messages} wiadomości...")
                    
                    try:
                        status, msg_data = mail.fetch(msg_id, '(RFC822)')
                        
                        if status != 'OK':
                            continue
                        
                        email_body = msg_data[0][1]
                        email_message = email.message_from_bytes(email_body)
                        
                        # Check message date
                        date_header = email_message.get('Date')
                        if not self._email_date_is_within_cutoff(date_header, cutoff_dt):
                            continue  # Skip messages older than cutoff
                        
                        # Get subject and sender
                        subject = self.decode_email_subject(email_message.get('Subject', ''))
                        sender = self.decode_email_subject(email_message.get('From', ''))
                        
                        # Check attachments
                        for part in email_message.walk():
                            if self.stop_event.is_set():
                                break
                            
                            if part.get_content_maintype() == 'multipart':
                                continue
                            
                            if part.get('Content-Disposition') is None:
                                continue
                            
                            filename = part.get_filename()
                            
                            # Check if it's a PDF and matches invoice pattern
                            if filename and filename.lower().endswith('.pdf'):
                                filename = self.decode_email_subject(filename)
                                
                                # Check if filename matches invoice pattern
                                if not self.matches_invoice_pattern(filename):
                                    continue
                                
                                # Save temporarily
                                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                                    tmp_file.write(part.get_payload(decode=True))
                                    tmp_path = tmp_file.name
                                
                                try:
                                    # Extract text from PDF
                                    pdf_text = self.extract_text_from_pdf(tmp_path)
                                    
                                    # Check if contains NIP (if searching by NIP)
                                    should_save = True
                                    if nip:
                                        should_save = self.search_nip_in_text(pdf_text, nip)
                                    
                                    if should_save:
                                        found_count += 1
                                        
                                        # Get unique filename based on policy
                                        safe_filename = self.make_safe_filename(filename)
                                        output_path = self.get_unique_filename(output_folder, safe_filename)
                                        
                                        # Save file with timestamp
                                        self._save_attachment_with_timestamp(
                                            part.get_payload(decode=True), 
                                            output_path, 
                                            email_message
                                        )
                                        
                                        # Format date for display
                                        email_date = ''
                                        try:
                                            if date_header:
                                                email_dt = parsedate_to_datetime(date_header)
                                                email_date = email_dt.strftime('%Y-%m-%d %H:%M')
                                        except:
                                            pass
                                        
                                        # Add to found invoices list
                                        self.add_found_invoice(
                                            date=email_date,
                                            sender=sender,
                                            subject=subject,
                                            filename=os.path.basename(output_path),
                                            file_path=output_path
                                        )
                                        
                                        # Push found file to queue for live display
                                        self.log_queue.put({
                                            'type': 'found',
                                            'path': output_path,
                                            'filename': os.path.basename(output_path)
                                        })
                                        
                                        self.safe_log(f"✓ Znaleziono: {filename} (z: {subject})")
                                
                                finally:
                                    # Remove temporary file - robust cleanup
                                    try:
                                        os.unlink(tmp_path)
                                    except (OSError, PermissionError, FileNotFoundError):
                                        # Silently ignore - temp file cleanup is not critical
                                        pass
                    
                    except Exception as e:
                        # Log error but continue processing other messages
                        self.safe_log(f"  Błąd przetwarzania wiadomości {msg_id}: {e}")
                        continue
                
                # Close current folder before moving to next
                mail.close()
                
            except Exception as e:
                self.safe_log(f"Błąd przeszukiwania folderu {folder}: {e}")
                continue
        
        mail.logout()
        
        # Refresh found invoices tab from main thread
        self.root.after(0, self.refresh_found_invoices)
        
        return found_count
    
    def _search_with_pop3_threaded(self, nip, output_folder, cutoff_dt):
        """Threaded POP3 search with stop event checking and timestamp setting"""
        found_count = 0
        
        # Connect to server
        if self.email_config['use_ssl']:
            mail = poplib.POP3_SSL(self.email_config['server'], int(self.email_config['port']))
        else:
            mail = poplib.POP3(self.email_config['server'], int(self.email_config['port']))
        
        mail.user(self.email_config['email'])
        mail.pass_(self.email_config['password'])
        
        self.safe_log("Połączono z serwerem POP3")
        
        # Get message list
        num_messages = len(mail.list()[1])
        
        self.safe_log(f"Znaleziono {num_messages} wiadomości do przeszukania")
        
        # Process messages with stop event checking
        for i in range(1, num_messages + 1):
            # Check if stop was requested
            if self.stop_event.is_set():
                break
            
            if i % 10 == 0:
                self.safe_log(f"Przetworzono {i}/{num_messages} wiadomości...")
            
            try:
                response, lines, octets = mail.retr(i)
                email_body = b'\n'.join(lines)
                email_message = email.message_from_bytes(email_body)
                
                # Check message date
                date_header = email_message.get('Date')
                if not self._email_date_is_within_cutoff(date_header, cutoff_dt):
                    continue  # Skip messages older than cutoff
                
                # Get subject
                subject = self.decode_email_subject(email_message.get('Subject', ''))
                
                # Check attachments
                for part in email_message.walk():
                    if self.stop_event.is_set():
                        break
                    
                    if part.get_content_maintype() == 'multipart':
                        continue
                    
                    if part.get('Content-Disposition') is None:
                        continue
                    
                    filename = part.get_filename()
                    
                    if filename and filename.lower().endswith('.pdf'):
                        filename = self.decode_email_subject(filename)
                        
                        # Save temporarily
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                            tmp_file.write(part.get_payload(decode=True))
                            tmp_path = tmp_file.name
                        
                        try:
                            # Extract text from PDF
                            pdf_text = self.extract_text_from_pdf(tmp_path)
                            
                            # Check if contains NIP
                            if self.search_nip_in_text(pdf_text, nip):
                                found_count += 1
                                
                                # Save file with timestamp
                                safe_filename = self.make_safe_filename(filename)
                                output_path = os.path.join(output_folder, f"{found_count}_{safe_filename}")
                                
                                self._save_attachment_with_timestamp(
                                    part.get_payload(decode=True), 
                                    output_path, 
                                    email_message
                                )
                                
                                self.safe_log(f"✓ Znaleziono: {filename} (z: {subject})")
                        
                        finally:
                            # Remove temporary file - robust cleanup
                            try:
                                os.unlink(tmp_path)
                            except (OSError, PermissionError, FileNotFoundError):
                                # Silently ignore - temp file cleanup is not critical
                                pass
            
            except Exception as e:
                # Log error but continue processing other messages
                self.safe_log(f"Błąd przetwarzania wiadomości {i}: {e}")
                continue
        
        mail.quit()
        
        return found_count
    
    def extract_text_from_pdf(self, pdf_path):
        """Ekstrakcja tekstu z pliku PDF"""
        text = ""
        
        # Próba z pdfplumber
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"Błąd pdfplumber: {e}")
        
        # Jeśli pdfplumber nie zadziałał, spróbuj PyPDF2
        if not text:
            try:
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
            except Exception as e:
                print(f"Błąd PyPDF2: {e}")
        
        return text
    
    def search_nip_in_text(self, text, nip):
        """Wyszukiwanie numeru NIP w tekście"""
        # Usuń wszystkie znaki niealfanumeryczne z NIP
        clean_nip = re.sub(r'[^0-9]', '', nip)
        
        # Usuń białe znaki z tekstu dla lepszego dopasowania
        clean_text = re.sub(r'\s+', '', text)
        
        # Szukaj NIP jako ciągłej liczby
        if clean_nip in clean_text:
            return True
        
        # Alternatywnie szukaj z możliwymi separatorami (tylko dla NIP o długości 10)
        if len(clean_nip) == 10:
            nip_patterns = [
                '-'.join([clean_nip[:3], clean_nip[3:6], clean_nip[6:8], clean_nip[8:]]),
                '-'.join([clean_nip[:3], clean_nip[3:]]),
            ]
            
            for pattern in nip_patterns:
                if pattern in text:
                    return True
        
        return False
    
    def search_invoices(self):
        """DEPRECATED: Główna funkcja wyszukiwania faktur (blocking, use start_search_thread instead)
        
        This method blocks the GUI during search. For GUI usage, use start_search_thread() instead.
        Kept for backwards compatibility and programmatic/testing usage.
        """
        nip = self.nip_entry.get().strip()
        output_folder = self.folder_entry.get().strip()
        
        if not nip:
            messagebox.showerror("Błąd", "Proszę podać numer NIP")
            return
        
        if not output_folder:
            messagebox.showerror("Błąd", "Proszę wybrać folder zapisu")
            return
        
        if not os.path.exists(output_folder):
            messagebox.showerror("Błąd", "Wybrany folder nie istnieje")
            return
        
        if not self.email_config.get('server'):
            messagebox.showerror("Błąd", "Proszę najpierw skonfigurować połączenie email")
            self.notebook.select(0)  # Przełącz na zakładkę konfiguracji
            return
        
        # Zaktualizuj search_config
        self.search_config = {
            'nip': nip,
            'output_folder': output_folder,
            'save_search_settings': self.save_search_config_var.get(),
            'range_1m': self.range_1m_var.get(),
            'range_3m': self.range_3m_var.get(),
            'range_6m': self.range_6m_var.get(),
            'range_week': self.range_week_var.get()
        }
        
        # Zapisz konfigurację jeśli zaznaczono checkbox
        if self.save_search_config_var.get():
            self.save_config()
        
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "Rozpoczynam wyszukiwanie...\n")
        
        # Informacja o zakresie czasowym
        cutoff_dt = self._get_cutoff_datetime()
        if cutoff_dt:
            self.results_text.insert(tk.END, f"Filtrowanie wiadomości starszych niż: {cutoff_dt.strftime('%Y-%m-%d')}\n")
        
        self.progress.start()
        self.root.update()
        
        try:
            found_count = 0
            processed_count = 0
            
            # Połącz z serwerem email
            protocol = self.email_config['protocol']
            
            if protocol == 'POP3':
                found_count = self.search_with_pop3(nip, output_folder)
            else:  # IMAP lub EXCHANGE
                found_count = self.search_with_imap(nip, output_folder)
            
            self.progress.stop()
            self.results_text.insert(tk.END, f"\n=== Zakończono wyszukiwanie ===\n")
            self.results_text.insert(tk.END, f"Znaleziono faktur z NIP {nip}: {found_count}\n")
            
            if found_count > 0:
                messagebox.showinfo("Sukces", f"Znaleziono {found_count} faktur(y) z podanym NIP.\nPliki zapisano w: {output_folder}")
            else:
                messagebox.showinfo("Informacja", "Nie znaleziono faktur z podanym NIP")
            
        except Exception as e:
            self.progress.stop()
            self.results_text.insert(tk.END, f"\nBŁĄD: {str(e)}\n")
            messagebox.showerror("Błąd", f"Wystąpił błąd podczas wyszukiwania:\n{str(e)}")
    
    def search_with_imap(self, nip, output_folder):
        """Wyszukiwanie przez IMAP"""
        found_count = 0
        cutoff_dt = self._get_cutoff_datetime()
        
        # Połącz z serwerem
        if self.email_config['use_ssl']:
            mail = imaplib.IMAP4_SSL(self.email_config['server'], self.email_config['port'])
        else:
            mail = imaplib.IMAP4(self.email_config['server'], self.email_config['port'])
        
        mail.login(self.email_config['email'], self.email_config['password'])
        
        self.results_text.insert(tk.END, "Połączono z serwerem IMAP\n")
        self.root.update()
        
        # Wybierz skrzynkę INBOX
        mail.select('INBOX')
        
        # Wyszukaj wszystkie wiadomości
        status, messages = mail.search(None, 'ALL')
        
        if status != 'OK':
            raise Exception("Nie można pobrać listy wiadomości")
        
        message_ids = messages[0].split()
        total_messages = len(message_ids)
        
        self.results_text.insert(tk.END, f"Znaleziono {total_messages} wiadomości do przeszukania\n")
        self.root.update()
        
        # Przeszukaj wiadomości
        for i, msg_id in enumerate(message_ids, 1):
            if i % 10 == 0:
                self.results_text.insert(tk.END, f"Przetworzono {i}/{total_messages} wiadomości...\n")
                self.root.update()
            
            try:
                status, msg_data = mail.fetch(msg_id, '(RFC822)')
                
                if status != 'OK':
                    continue
                
                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)
                
                # Sprawdź datę wiadomości
                date_header = email_message.get('Date')
                if not self._email_date_is_within_cutoff(date_header, cutoff_dt):
                    continue  # Pomiń wiadomości starsze niż cutoff
                
                # Pobierz temat
                subject = self.decode_email_subject(email_message.get('Subject', ''))
                
                # Sprawdź załączniki
                for part in email_message.walk():
                    if part.get_content_maintype() == 'multipart':
                        continue
                    
                    if part.get('Content-Disposition') is None:
                        continue
                    
                    filename = part.get_filename()
                    
                    if filename and filename.lower().endswith('.pdf'):
                        filename = self.decode_email_subject(filename)
                        
                        # Zapisz tymczasowo PDF
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                            tmp_file.write(part.get_payload(decode=True))
                            tmp_path = tmp_file.name
                        
                        try:
                            # Ekstrakcja tekstu z PDF
                            pdf_text = self.extract_text_from_pdf(tmp_path)
                            
                            # Sprawdź czy zawiera NIP
                            if self.search_nip_in_text(pdf_text, nip):
                                found_count += 1
                                
                                # Zapisz plik
                                safe_filename = self.make_safe_filename(filename)
                                output_path = os.path.join(output_folder, f"{found_count}_{safe_filename}")
                                
                                with open(output_path, 'wb') as f:
                                    f.write(part.get_payload(decode=True))
                                
                                self.results_text.insert(tk.END, f"✓ Znaleziono: {filename} (z: {subject})\n")
                                self.root.update()
                        
                        finally:
                            # Usuń plik tymczasowy
                            try:
                                os.unlink(tmp_path)
                            except (OSError, PermissionError):
                                pass
            
            except Exception as e:
                print(f"Błąd przetwarzania wiadomości {msg_id}: {e}")
                continue
        
        mail.close()
        mail.logout()
        
        return found_count
    
    def search_with_pop3(self, nip, output_folder):
        """Wyszukiwanie przez POP3"""
        found_count = 0
        cutoff_dt = self._get_cutoff_datetime()
        
        # Połącz z serwerem
        if self.email_config['use_ssl']:
            mail = poplib.POP3_SSL(self.email_config['server'], self.email_config['port'])
        else:
            mail = poplib.POP3(self.email_config['server'], self.email_config['port'])
        
        mail.user(self.email_config['email'])
        mail.pass_(self.email_config['password'])
        
        self.results_text.insert(tk.END, "Połączono z serwerem POP3\n")
        self.root.update()
        
        # Pobierz listę wiadomości
        num_messages = len(mail.list()[1])
        
        self.results_text.insert(tk.END, f"Znaleziono {num_messages} wiadomości do przeszukania\n")
        self.root.update()
        
        # Przeszukaj wiadomości
        for i in range(1, num_messages + 1):
            if i % 10 == 0:
                self.results_text.insert(tk.END, f"Przetworzono {i}/{num_messages} wiadomości...\n")
                self.root.update()
            
            try:
                response, lines, octets = mail.retr(i)
                email_body = b'\n'.join(lines)
                email_message = email.message_from_bytes(email_body)
                
                # Sprawdź datę wiadomości
                date_header = email_message.get('Date')
                if not self._email_date_is_within_cutoff(date_header, cutoff_dt):
                    continue  # Pomiń wiadomości starsze niż cutoff
                
                # Pobierz temat
                subject = self.decode_email_subject(email_message.get('Subject', ''))
                
                # Sprawdź załączniki
                for part in email_message.walk():
                    if part.get_content_maintype() == 'multipart':
                        continue
                    
                    if part.get('Content-Disposition') is None:
                        continue
                    
                    filename = part.get_filename()
                    
                    if filename and filename.lower().endswith('.pdf'):
                        filename = self.decode_email_subject(filename)
                        
                        # Zapisz tymczasowo PDF
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                            tmp_file.write(part.get_payload(decode=True))
                            tmp_path = tmp_file.name
                        
                        try:
                            # Ekstrakcja tekstu z PDF
                            pdf_text = self.extract_text_from_pdf(tmp_path)
                            
                            # Sprawdź czy zawiera NIP
                            if self.search_nip_in_text(pdf_text, nip):
                                found_count += 1
                                
                                # Zapisz plik
                                safe_filename = self.make_safe_filename(filename)
                                output_path = os.path.join(output_folder, f"{found_count}_{safe_filename}")
                                
                                with open(output_path, 'wb') as f:
                                    f.write(part.get_payload(decode=True))
                                
                                self.results_text.insert(tk.END, f"✓ Znaleziono: {filename} (z: {subject})\n")
                                self.root.update()
                        
                        finally:
                            # Usuń plik tymczasowy
                            try:
                                os.unlink(tmp_path)
                            except (OSError, PermissionError):
                                pass
            
            except Exception as e:
                print(f"Błąd przetwarzania wiadomości {i}: {e}")
                continue
        
        mail.quit()
        
        return found_count
    
    def decode_email_subject(self, subject):
        """Dekodowanie tematu email"""
        if not subject:
            return ""
        
        decoded_parts = []
        for part, encoding in decode_header(subject):
            if isinstance(part, bytes):
                try:
                    decoded_parts.append(part.decode(encoding or 'utf-8'))
                except (UnicodeDecodeError, LookupError):
                    decoded_parts.append(part.decode('utf-8', errors='ignore'))
            else:
                decoded_parts.append(str(part))
        
        return ''.join(decoded_parts)
    
    def make_safe_filename(self, filename):
        """Tworzenie bezpiecznej nazwy pliku"""
        # Weź tylko nazwę pliku (bez ścieżki)
        filename = os.path.basename(filename)
        
        # Usuń niebezpieczne znaki
        safe_chars = '-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789ąćęłńóśźżĄĆĘŁŃÓŚŹŻ'
        safe_filename = ''.join(c for c in filename if c in safe_chars)
        
        # Ogranicz długość
        if len(safe_filename) > 200:
            name, ext = os.path.splitext(safe_filename)
            safe_filename = name[:200-len(ext)] + ext
        
        return safe_filename if safe_filename else 'faktura.pdf'


def main():
    """Uruchomienie aplikacji"""
    root = tk.Tk()
    app = EmailInvoiceFinderApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
