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
from datetime import datetime, timedelta, date
from email.utils import parsedate_to_datetime
import threading
import queue

# Import EmailAccountManager - use direct file import to avoid circular dependency
import importlib.util
_email_account_manager_path = Path(__file__).parent / 'poczta_faktury' / 'email_account_manager.py'
if _email_account_manager_path.exists():
    _spec = importlib.util.spec_from_file_location("email_account_manager", _email_account_manager_path)
    _email_account_manager_module = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_email_account_manager_module)
    EmailAccountManager = _email_account_manager_module.EmailAccountManager
else:
    EmailAccountManager = None

# Safe import for tkcalendar DateEntry
try:
    from tkcalendar import DateEntry
    TKCALENDAR_AVAILABLE = True
except ImportError:
    TKCALENDAR_AVAILABLE = False
    DateEntry = None

# Safe import for znalezione window
try:
    from gui.search_results.znalezione_window import open_znalezione_window
except Exception:
    open_znalezione_window = None

# Safe import for logger with extended functionality
try:
    from gui.logger import log, set_level, init_from_config, save_level_to_config, LOG_LEVEL_NAMES, get_level
except ImportError:
    # fallback: import existing simple log function
    from gui.logger import log
    LOG_LEVEL_NAMES = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']

# Import dialog utilities
try:
    from gui.dialog_utils import center_and_clamp_window, safe_show_error, safe_show_info, safe_show_warning
except ImportError:
    # Fallback if gui.dialog_utils is not available - define functions inline
    def center_and_clamp_window(win: tk.Toplevel, parent: tk.Widget = None, max_ratio: float = 0.95):
        """Center and clamp a Toplevel window to the visible screen area."""
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

# Plik konfiguracyjny
CONFIG_FILE = Path.home() / '.poczta_faktury_config.json'

# Plik z wersją aplikacji
VERSION_FILE = Path(__file__).parent / 'version.txt'

# Gmail authentication constants
GOOGLE_APP_PASSWORDS_URL = 'https://myaccount.google.com/apppasswords'
GOOGLE_APP_PASSWORDS_URL_DISPLAY = 'myaccount.google.com/apppasswords'

# Gmail-specific authentication error keywords (highly specific to Gmail)
GMAIL_SPECIFIC_ERROR_KEYWORDS = [
    'application-specific password',
    'app-specific password',
    'app-specific password required',
    'app password',
    'please use an app password',
]

# Generic authentication error keywords (could occur with Gmail or other providers)
GMAIL_GENERIC_ERROR_KEYWORDS = [
    'username and password not accepted',
    '[auth]',
    'invalid credentials'
]

# Combined list for checking
GMAIL_AUTH_ERROR_KEYWORDS = GMAIL_SPECIFIC_ERROR_KEYWORDS + GMAIL_GENERIC_ERROR_KEYWORDS

# Gmail authentication error message template
GMAIL_AUTH_ERROR_MESSAGE_TEMPLATE = """❌ BŁĄD UWIERZYTELNIANIA GMAIL

Gmail wymaga użycia HASŁA APLIKACJI zamiast zwykłego hasła konta.

📋 Jak wygenerować hasło aplikacji:

1. Przejdź do: {url}
2. Zaloguj się do swojego konta Google
3. Upewnij się, że weryfikacja dwuetapowa jest włączona
4. Wybierz: Aplikacja = 'Poczta', Urządzenie = 'Komputer'
5. Kliknij 'Generuj'
6. Skopiuj 16-znakowe hasło (bez spacji)
7. Użyj tego hasła w polu 'Hasło' w tej aplikacji

📖 Szczegółowa instrukcja: Zobacz plik USAGE.md lub README.md

Oryginalny błąd: {error}"""


def is_gmail_server(server):
    """
    Check if the given server hostname is a Gmail server.
    
    This function checks if the server is exactly 'gmail.com' or ends with '.gmail.com'
    (e.g., imap.gmail.com, pop.gmail.com, smtp.gmail.com).
    
    Args:
        server (str): Server hostname to check
        
    Returns:
        bool: True if the server is a Gmail server, False otherwise
        
    Examples:
        >>> is_gmail_server('imap.gmail.com')
        True
        >>> is_gmail_server('gmail.com')
        True
        >>> is_gmail_server('notgmail.com')
        False
        >>> is_gmail_server('gmail.com.attacker.com')
        False
    """
    if not server:
        return False
    server_lower = server.lower()
    return server_lower == 'gmail.com' or server_lower.endswith('.gmail.com')


class EmailInvoiceFinderApp:
    """Główna aplikacja do wyszukiwania faktur"""
    
    def __init__(self, root):
        self.root = root
        
        # Wczytaj wersję aplikacji
        self.version = self._load_version()
        
        # Ustaw tytuł okna z wersją
        self._update_window_title()
        
        # Enable window resizing for better element display
        self.root.minsize(600, 400)  # Set minimum size to prevent too small window
        self.root.resizable(True, True)  # Enable resizing in both directions
        
        # Initialize EmailAccountManager
        if EmailAccountManager:
            self.account_manager = EmailAccountManager(CONFIG_FILE)
        else:
            self.account_manager = None
        
        # Konfiguracja email (kept for backward compatibility during transition)
        self.email_config = {
            'protocol': 'IMAP',
            'server': '',
            'port': '',
            'email': '',
            'password': '',
            'use_ssl': True,
            'save_email_settings': False,
            'pdf_engine': 'pdfplumber'  # PDF engine: pdfplumber or pdfminer.six
        }
        
        # Initialize PDF engine variable early (before UI creation) to avoid hasattr checks
        self.pdf_engine_var = None
        
        # Ustawienia wyszukiwania
        self.search_config = {
            'nip': '',
            'output_folder': '',
            'save_search_settings': False,
            'date_from': None,  # Custom date range: start date (ISO format YYYY-MM-DD or None)
            'date_to': None     # Custom date range: end date (ISO format YYYY-MM-DD or None)
        }
        
        # Threading controls for non-blocking search
        self.search_thread = None
        self.stop_event = threading.Event()
        self.log_queue = queue.Queue()
        
        # Initialize log level from config (if set)
        try:
            init_from_config()
        except Exception:
            pass
        
        # Wczytaj konfigurację z pliku
        self.load_config()
        
        self.create_widgets()
        
        # Dynamically size window to fit content (after widgets are created)
        self.root.update_idletasks()
        req_w = self.root.winfo_reqwidth()
        req_h = self.root.winfo_reqheight()
        final_w = max(req_w, 600)
        final_h = max(req_h, 400)
        self.root.geometry(f"{final_w}x{final_h}")
        
        # Uruchom watcher pliku wersji
        self.root.after(5000, self._watch_version_file)
    
    def create_widgets(self):
        """Tworzenie interfejsu użytkownika"""
        # Notebook (zakładki)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Zakładka 1: Ustawienia (poprzednio: Konfiguracja email)
        self.config_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.config_frame, text="Ustawienia")
        self.create_email_config_tab()
        
        # Zakładka 2: Wyszukiwanie
        self.search_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.search_frame, text="Wyszukiwanie")
        self.create_search_tab()
        
        # Zakładka 3: O programie
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
        
        # Gmail info label
        gmail_info_frame = ttk.Frame(self.config_frame)
        gmail_info_frame.grid(row=5, column=0, columnspan=2, sticky='w', padx=10, pady=(0, 5))
        
        info_icon = ttk.Label(gmail_info_frame, text="ℹ️", font=("TkDefaultFont", 10))
        info_icon.pack(side='left', padx=(0, 5))
        
        gmail_info_label = ttk.Label(
            gmail_info_frame, 
            text=f"Gmail: Użyj hasła aplikacji zamiast zwykłego hasła ({GOOGLE_APP_PASSWORDS_URL_DISPLAY})",
            font=("TkDefaultFont", 8),
            foreground="#0066cc"
        )
        gmail_info_label.pack(side='left')
        
        # Pokaż hasło
        self.show_password_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self.config_frame, text="Pokaż hasło", 
                       variable=self.show_password_var,
                       command=self.toggle_show_password).grid(row=6, column=0, columnspan=2, padx=10, pady=5)
        
        # SSL
        self.ssl_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.config_frame, text="Użyj SSL/TLS", 
                       variable=self.ssl_var).grid(row=7, column=0, columnspan=2, padx=10, pady=5)
        
        # Zapisz ustawienia
        self.save_email_config_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self.config_frame, text="Zapisz ustawienia", 
                       variable=self.save_email_config_var).grid(row=8, column=0, columnspan=2, padx=10, pady=5)
        
        # Przycisk testowania połączenia
        ttk.Button(self.config_frame, text="Testuj połączenie", 
                  command=self.test_connection).grid(row=9, column=0, columnspan=2, pady=20)
        
        # Status
        self.status_label = ttk.Label(self.config_frame, text="", foreground="blue")
        self.status_label.grid(row=10, column=0, columnspan=2, padx=10, pady=5)
        
        # Separator between mail config and PDF engine settings
        ttk.Separator(self.config_frame, orient='horizontal').grid(row=11, column=0, columnspan=2, sticky='ew', padx=10, pady=20)
        
        # PDF Engine selection - Create a frame to hold both the label and current engine display
        pdf_header_frame = ttk.Frame(self.config_frame)
        pdf_header_frame.grid(row=12, column=0, columnspan=2, sticky='w', padx=10, pady=(10, 5))
        
        ttk.Label(pdf_header_frame, text="Silnik PDF:", font=("TkDefaultFont", 10, "bold")).pack(side='left')
        
        # Create label for displaying current PDF engine value (will be updated after config is loaded)
        self.current_engine_label = ttk.Label(
            pdf_header_frame, 
            text=f" {self.email_config.get('pdf_engine', 'pdfplumber')}",
            font=("TkDefaultFont", 8),
            foreground='#008000'  # Green color for consistency with previous implementation
        )
        self.current_engine_label.pack(side='left', padx=5)
        
        ttk.Label(self.config_frame, text="Wybierz silnik ekstrakcji tekstu:").grid(row=13, column=0, sticky='w', padx=10, pady=5)
        self.pdf_engine_var = tk.StringVar(value='pdfplumber')
        # Bind callback to update the current engine display when selection changes
        self.pdf_engine_var.trace_add('write', self._on_pdf_engine_changed)
        pdf_engine_combo = ttk.Combobox(self.config_frame, textvariable=self.pdf_engine_var, 
                                        values=['pdfplumber', 'pdfminer.six'], 
                                        state='readonly', width=37)
        pdf_engine_combo.grid(row=13, column=1, sticky='ew', padx=10, pady=5)
        
        # Separator before log level settings
        ttk.Separator(self.config_frame, orient='horizontal').grid(row=14, column=0, columnspan=2, sticky='ew', padx=10, pady=20)
        
        # Log Level selection
        ttk.Label(self.config_frame, text="Poziom logów:").grid(row=15, column=0, sticky='w', padx=10, pady=5)
        try:
            level_values = LOG_LEVEL_NAMES
            self.log_level_var = tk.StringVar(value=get_level())
        except (NameError, AttributeError):
            # Fallback if LOG_LEVEL_NAMES or get_level not available
            level_values = LOG_LEVEL_NAMES  # Use fallback from import section
            self.log_level_var = tk.StringVar(value='INFO')
        
        log_level_cb = ttk.Combobox(self.config_frame, values=level_values, textvariable=self.log_level_var, 
                                     state='readonly', width=37)
        log_level_cb.grid(row=15, column=1, sticky='ew', padx=10, pady=5)
        log_level_cb.bind("<<ComboboxSelected>>", self._on_log_level_change)
        
        # Separator before account management
        ttk.Separator(self.config_frame, orient='horizontal').grid(row=16, column=0, columnspan=2, sticky='ew', padx=10, pady=20)
        
        # Account Management Section
        if self.account_manager:
            self._create_account_management_section()
        
        self.config_frame.columnconfigure(1, weight=1)
    
    def _create_account_management_section(self):
        """Tworzenie sekcji zarządzania kontami email"""
        # Account Management Header
        accounts_header_frame = ttk.Frame(self.config_frame)
        accounts_header_frame.grid(row=17, column=0, columnspan=2, sticky='ew', padx=10, pady=(10, 5))
        
        ttk.Label(accounts_header_frame, text="Zarządzanie kontami email:", 
                 font=("TkDefaultFont", 10, "bold")).pack(side='left')
        
        # Active account selector
        active_account_frame = ttk.Frame(self.config_frame)
        active_account_frame.grid(row=18, column=0, columnspan=2, sticky='ew', padx=10, pady=5)
        
        ttk.Label(active_account_frame, text="Aktywne konto:").pack(side='left', padx=(0, 5))
        
        self.active_account_var = tk.StringVar()
        self.active_account_combo = ttk.Combobox(active_account_frame, 
                                                  textvariable=self.active_account_var,
                                                  state='readonly', width=40)
        self.active_account_combo.pack(side='left', fill='x', expand=True)
        self.active_account_combo.bind("<<ComboboxSelected>>", self._on_active_account_changed)
        
        # Account list and buttons frame
        accounts_list_frame = ttk.Frame(self.config_frame)
        accounts_list_frame.grid(row=19, column=0, columnspan=2, sticky='nsew', padx=10, pady=5)
        
        # Listbox with scrollbar
        list_scroll_frame = ttk.Frame(accounts_list_frame)
        list_scroll_frame.pack(side='left', fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(list_scroll_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.accounts_listbox = tk.Listbox(list_scroll_frame, 
                                           yscrollcommand=scrollbar.set,
                                           height=5, width=40)
        self.accounts_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.accounts_listbox.yview)
        
        # Buttons frame
        buttons_frame = ttk.Frame(accounts_list_frame)
        buttons_frame.pack(side='right', fill='y', padx=(10, 0))
        
        ttk.Button(buttons_frame, text="Dodaj konto", 
                  command=self._add_account_dialog).pack(pady=2, fill='x')
        ttk.Button(buttons_frame, text="Edytuj konto", 
                  command=self._edit_account_dialog).pack(pady=2, fill='x')
        ttk.Button(buttons_frame, text="Usuń konto", 
                  command=self._delete_account).pack(pady=2, fill='x')
        ttk.Button(buttons_frame, text="Załaduj do pól", 
                  command=self._load_account_to_fields).pack(pady=2, fill='x')
        
        # Info label
        self.account_info_label = ttk.Label(self.config_frame, text="", foreground="blue")
        self.account_info_label.grid(row=20, column=0, columnspan=2, padx=10, pady=5)
        
        # Refresh account list
        self._refresh_accounts_list()
    
    def create_search_tab(self):
        """Tworzenie zakładki wyszukiwania"""
        # NIP
        ttk.Label(self.search_frame, text="Wyszukaj:").grid(row=0, column=0, sticky='w', padx=10, pady=5)
        self.nip_entry = ttk.Entry(self.search_frame, width=40)
        self.nip_entry.grid(row=0, column=1, sticky='ew', padx=10, pady=5)
        
        # Folder wyjściowy
        ttk.Label(self.search_frame, text="Folder zapisu:").grid(row=1, column=0, sticky='w', padx=10, pady=5)
        
        folder_frame = ttk.Frame(self.search_frame)
        folder_frame.grid(row=1, column=1, sticky='ew', padx=10, pady=5)
        
        self.folder_entry = ttk.Entry(folder_frame, width=30)
        self.folder_entry.pack(side='left', fill='x', expand=True)
        
        ttk.Button(folder_frame, text="Przeglądaj...", 
                  command=self.browse_folder).pack(side='left', padx=5)
        
        # Custom date range picker (Od - Do)
        date_range_frame = ttk.LabelFrame(self.search_frame, text="Zakres dat", padding=10)
        date_range_frame.grid(row=2, column=0, columnspan=2, sticky='ew', padx=10, pady=5)
        
        if TKCALENDAR_AVAILABLE:
            # Date "Od" (From)
            ttk.Label(date_range_frame, text="Od:").pack(side='left', padx=(0, 5))
            try:
                self.date_from_entry = DateEntry(date_range_frame, width=12, background='darkblue',
                                                 foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd',
                                                 locale='pl_PL', showweeknumbers=False)
            except Exception:
                # Fallback to default locale if pl_PL is not available
                self.date_from_entry = DateEntry(date_range_frame, width=12, background='darkblue',
                                                 foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd',
                                                 showweeknumbers=False)
            self.date_from_entry.pack(side='left', padx=5)
            # Set to None initially (will be handled in validation)
            self.date_from_entry.delete(0, tk.END)
            
            # Date "Do" (To)
            ttk.Label(date_range_frame, text="Do:").pack(side='left', padx=(10, 5))
            try:
                self.date_to_entry = DateEntry(date_range_frame, width=12, background='darkblue',
                                               foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd',
                                               locale='pl_PL', showweeknumbers=False)
            except Exception:
                # Fallback to default locale if pl_PL is not available
                self.date_to_entry = DateEntry(date_range_frame, width=12, background='darkblue',
                                               foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd',
                                               showweeknumbers=False)
            self.date_to_entry.pack(side='left', padx=5)
            # Set to today by default
            self.date_to_entry.set_date(date.today())
            
            # Clear range button
            ttk.Button(date_range_frame, text="Wyczyść zakres", 
                      command=self.clear_date_range).pack(side='left', padx=10)
            
            # Info label for date range
            self.date_range_info_label = ttk.Label(date_range_frame, text="", foreground="blue", font=('Arial', 8))
            self.date_range_info_label.pack(side='left', padx=10)
        else:
            # Fallback if tkcalendar is not available
            ttk.Label(date_range_frame, text="Kalendarz niedostępny - zainstaluj tkcalendar", 
                     foreground="red").pack(side='left', padx=5)
            self.date_from_entry = None
            self.date_to_entry = None
            self.date_range_info_label = None
        
        # Zapisz ustawienia
        self.save_search_config_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self.search_frame, text="Zapisz ustawienia", 
                       variable=self.save_search_config_var).grid(row=3, column=0, columnspan=2, padx=10, pady=5)
        
        # Sortuj w folderach - checkbox umieszczony w zakładce "Wyszukiwanie"
        # Gdy zaznaczony, podczas zapisu wyników utworzone zostaną podfoldery MM.YYYY (np. 10.2025)
        self.sort_in_folders_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self.search_frame, text="Sortuj w folderach", 
                       variable=self.sort_in_folders_var).grid(row=4, column=0, columnspan=2, padx=10, pady=5, sticky='w')
        
        # Przyciski wyszukiwania
        button_frame = ttk.Frame(self.search_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        self.search_button = ttk.Button(button_frame, text="Szukaj faktur", 
                   command=self.start_search_thread)
        self.search_button.pack(side='left', padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="Przerwij", 
                   command=self.stop_search, state='disabled')
        self.stop_button.pack(side='left', padx=5)
        
        # Przycisk "Znalezione" - okno wyników wyszukiwania
        def _open_znalezione_with_criteria():
            # Get date_from from date picker if available
            date_from_dt = None
            if TKCALENDAR_AVAILABLE and hasattr(self, 'date_from_entry') and self.date_from_entry:
                date_from_str = self.date_from_entry.get().strip()
                if date_from_str:
                    try:
                        date_from = self.date_from_entry.get_date()
                        date_from_dt = datetime.combine(date_from, datetime.min.time())
                    except Exception:
                        pass
            
            criteria = {
                'nip': self.nip_entry.get() if hasattr(self, 'nip_entry') else '',
                'output_folder': self.folder_entry.get() if hasattr(self, 'folder_entry') else '',
                'date_from': date_from_dt,
                'connection': getattr(self, 'email_connection', None)
            }
            if open_znalezione_window:
                open_znalezione_window(self.root, criteria)
            else:
                messagebox.showinfo("Info", "Okno Znalezione jest niedostępne (brak modułu)", parent=self.root)
        
        self.znalezione_button = ttk.Button(button_frame, text="Znalezione ➜",
                                             command=_open_znalezione_with_criteria)
        self.znalezione_button.pack(side='left', padx=5)
        
        # Selected date range display (above progress bar)
        self.selected_range_label = ttk.Label(self.search_frame, text="", foreground="green", font=('Arial', 9, 'bold'))
        self.selected_range_label.grid(row=5, column=0, columnspan=2, sticky='w', padx=10, pady=2)
        
        # Pasek postępu
        self.progress = ttk.Progressbar(self.search_frame, mode='indeterminate')
        self.progress.grid(row=6, column=0, columnspan=2, sticky='ew', padx=10, pady=5)
        
        # Wyniki
        ttk.Label(self.search_frame, text="Wyniki:").grid(row=7, column=0, columnspan=2, sticky='w', padx=10, pady=5)
        
        self.results_text = scrolledtext.ScrolledText(self.search_frame, height=20, width=70)
        self.results_text.grid(row=8, column=0, columnspan=2, sticky='nsew', padx=10, pady=5)
        
        self.search_frame.columnconfigure(1, weight=1)
        self.search_frame.rowconfigure(8, weight=1)
    
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
        """Aktualizacja tytułu okna z numerem wersji (z wersją i numerem PR jeśli dostępny)."""
        version_str = None
        try:
            # Spróbuj użyć modułu version_info (jeśli dodany do repo)
            from version_info import get_version_string
            version_str = get_version_string()
        except (ImportError, AttributeError):
            version_str = None

        if not version_str:
            # Fallback - użyj istniejącej self.version
            version_str = f"ver. {self.version}"

        self.root.title(f"Poczta Faktury - Wyszukiwanie faktur po NIP  {version_str}")
    
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
    
    def _refresh_accounts_list(self):
        """Odświeżenie listy kont w UI"""
        if not self.account_manager:
            return
        
        # Clear listbox
        self.accounts_listbox.delete(0, tk.END)
        
        # Get accounts
        accounts = self.account_manager.get_accounts()
        
        # Update listbox
        for account in accounts:
            name = account.get('name', account.get('email', 'Unnamed'))
            email = account.get('email', '')
            display_text = f"{name} ({email})"
            self.accounts_listbox.insert(tk.END, display_text)
        
        # Update active account combo
        account_emails = [acc.get('email', '') for acc in accounts]
        self.active_account_combo['values'] = account_emails
        
        # Set active account in combo
        active = self.account_manager.get_active_account()
        if active:
            self.active_account_var.set(active.get('email', ''))
        elif account_emails:
            self.active_account_var.set(account_emails[0])
    
    def _on_active_account_changed(self, event=None):
        """Callback gdy użytkownik zmieni aktywne konto"""
        if not self.account_manager:
            return
        
        selected_email = self.active_account_var.get()
        if selected_email:
            if self.account_manager.set_active_account(selected_email):
                self.account_info_label.config(text=f"Aktywne konto ustawione na: {selected_email}", 
                                              foreground="green")
                # Load account to fields
                self._load_account_to_fields_by_email(selected_email)
            else:
                self.account_info_label.config(text="Błąd przy ustawianiu aktywnego konta", 
                                              foreground="red")
    
    def _add_account_dialog(self):
        """Dialog dodawania nowego konta"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Dodaj nowe konto")
        dialog.transient(self.root)
        
        # Account fields
        fields = {}
        row = 0
        
        ttk.Label(dialog, text="Nazwa konta:").grid(row=row, column=0, sticky='w', padx=10, pady=5)
        fields['name'] = ttk.Entry(dialog, width=40)
        fields['name'].grid(row=row, column=1, sticky='ew', padx=10, pady=5)
        row += 1
        
        ttk.Label(dialog, text="Email:").grid(row=row, column=0, sticky='w', padx=10, pady=5)
        fields['email'] = ttk.Entry(dialog, width=40)
        fields['email'].grid(row=row, column=1, sticky='ew', padx=10, pady=5)
        row += 1
        
        ttk.Label(dialog, text="Protokół:").grid(row=row, column=0, sticky='w', padx=10, pady=5)
        protocol_var = tk.StringVar(value='IMAP')
        protocol_frame = ttk.Frame(dialog)
        protocol_frame.grid(row=row, column=1, sticky='w', padx=10, pady=5)
        ttk.Radiobutton(protocol_frame, text="IMAP", variable=protocol_var, value='IMAP').pack(side='left')
        ttk.Radiobutton(protocol_frame, text="POP3", variable=protocol_var, value='POP3').pack(side='left')
        ttk.Radiobutton(protocol_frame, text="Exchange", variable=protocol_var, value='EXCHANGE').pack(side='left')
        fields['protocol'] = protocol_var
        row += 1
        
        ttk.Label(dialog, text="Serwer:").grid(row=row, column=0, sticky='w', padx=10, pady=5)
        fields['server'] = ttk.Entry(dialog, width=40)
        fields['server'].grid(row=row, column=1, sticky='ew', padx=10, pady=5)
        row += 1
        
        ttk.Label(dialog, text="Port:").grid(row=row, column=0, sticky='w', padx=10, pady=5)
        fields['port'] = ttk.Entry(dialog, width=40)
        fields['port'].insert(0, "993")
        fields['port'].grid(row=row, column=1, sticky='ew', padx=10, pady=5)
        row += 1
        
        ttk.Label(dialog, text="Hasło:").grid(row=row, column=0, sticky='w', padx=10, pady=5)
        fields['password'] = ttk.Entry(dialog, width=40, show='*')
        fields['password'].grid(row=row, column=1, sticky='ew', padx=10, pady=5)
        row += 1
        
        ssl_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(dialog, text="Użyj SSL/TLS", variable=ssl_var).grid(
            row=row, column=0, columnspan=2, padx=10, pady=5)
        fields['use_ssl'] = ssl_var
        row += 1
        
        ttk.Label(dialog, text="Silnik PDF:").grid(row=row, column=0, sticky='w', padx=10, pady=5)
        pdf_engine_var = tk.StringVar(value='pdfplumber')
        pdf_combo = ttk.Combobox(dialog, textvariable=pdf_engine_var, 
                                values=['pdfplumber', 'pdfminer.six'], state='readonly', width=37)
        pdf_combo.grid(row=row, column=1, sticky='ew', padx=10, pady=5)
        fields['pdf_engine'] = pdf_engine_var
        row += 1
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=row, column=0, columnspan=2, pady=20)
        
        def save_account():
            account = {
                'name': fields['name'].get().strip(),
                'email': fields['email'].get().strip(),
                'protocol': fields['protocol'].get(),
                'server': fields['server'].get().strip(),
                'port': fields['port'].get().strip(),
                'password': fields['password'].get(),
                'use_ssl': fields['use_ssl'].get(),
                'pdf_engine': fields['pdf_engine'].get()
            }
            
            if not account['email']:
                messagebox.showerror("Błąd", "Email jest wymagany", parent=dialog)
                return
            
            if not account['name']:
                account['name'] = account['email']
            
            try:
                if self.account_manager.add_account(account):
                    self._refresh_accounts_list()
                    self.account_info_label.config(text=f"Dodano konto: {account['email']}", 
                                                  foreground="green")
                    dialog.destroy()
                else:
                    messagebox.showerror("Błąd", "Konto o tym adresie email już istnieje", parent=dialog)
            except Exception as e:
                messagebox.showerror("Błąd", f"Nie udało się dodać konta:\n{str(e)}", parent=dialog)
        
        ttk.Button(button_frame, text="Zapisz", command=save_account).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Anuluj", command=dialog.destroy).pack(side='left', padx=5)
        
        dialog.columnconfigure(1, weight=1)
        
        # Center and clamp the dialog window
        center_and_clamp_window(dialog, parent=self.root)
        dialog.grab_set()
    
    def _edit_account_dialog(self):
        """Dialog edycji istniejącego konta"""
        selection = self.accounts_listbox.curselection()
        if not selection:
            messagebox.showwarning("Ostrzeżenie", "Proszę wybrać konto do edycji", parent=self.root)
            return
        
        # Get selected account
        accounts = self.account_manager.get_accounts()
        account = accounts[selection[0]]
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Edytuj konto: {account.get('email')}")
        dialog.transient(self.root)
        
        # Account fields (similar to add dialog but pre-filled)
        fields = {}
        row = 0
        
        ttk.Label(dialog, text="Nazwa konta:").grid(row=row, column=0, sticky='w', padx=10, pady=5)
        fields['name'] = ttk.Entry(dialog, width=40)
        fields['name'].insert(0, account.get('name', ''))
        fields['name'].grid(row=row, column=1, sticky='ew', padx=10, pady=5)
        row += 1
        
        ttk.Label(dialog, text="Email:").grid(row=row, column=0, sticky='w', padx=10, pady=5)
        email_label = ttk.Label(dialog, text=account.get('email', ''), foreground='gray')
        email_label.grid(row=row, column=1, sticky='w', padx=10, pady=5)
        row += 1
        
        ttk.Label(dialog, text="Protokół:").grid(row=row, column=0, sticky='w', padx=10, pady=5)
        protocol_var = tk.StringVar(value=account.get('protocol', 'IMAP'))
        protocol_frame = ttk.Frame(dialog)
        protocol_frame.grid(row=row, column=1, sticky='w', padx=10, pady=5)
        ttk.Radiobutton(protocol_frame, text="IMAP", variable=protocol_var, value='IMAP').pack(side='left')
        ttk.Radiobutton(protocol_frame, text="POP3", variable=protocol_var, value='POP3').pack(side='left')
        ttk.Radiobutton(protocol_frame, text="Exchange", variable=protocol_var, value='EXCHANGE').pack(side='left')
        fields['protocol'] = protocol_var
        row += 1
        
        ttk.Label(dialog, text="Serwer:").grid(row=row, column=0, sticky='w', padx=10, pady=5)
        fields['server'] = ttk.Entry(dialog, width=40)
        fields['server'].insert(0, account.get('server', ''))
        fields['server'].grid(row=row, column=1, sticky='ew', padx=10, pady=5)
        row += 1
        
        ttk.Label(dialog, text="Port:").grid(row=row, column=0, sticky='w', padx=10, pady=5)
        fields['port'] = ttk.Entry(dialog, width=40)
        fields['port'].insert(0, account.get('port', '993'))
        fields['port'].grid(row=row, column=1, sticky='ew', padx=10, pady=5)
        row += 1
        
        ttk.Label(dialog, text="Hasło:").grid(row=row, column=0, sticky='w', padx=10, pady=5)
        fields['password'] = ttk.Entry(dialog, width=40, show='*')
        fields['password'].insert(0, account.get('password', ''))
        fields['password'].grid(row=row, column=1, sticky='ew', padx=10, pady=5)
        row += 1
        
        ssl_var = tk.BooleanVar(value=account.get('use_ssl', True))
        ttk.Checkbutton(dialog, text="Użyj SSL/TLS", variable=ssl_var).grid(
            row=row, column=0, columnspan=2, padx=10, pady=5)
        fields['use_ssl'] = ssl_var
        row += 1
        
        ttk.Label(dialog, text="Silnik PDF:").grid(row=row, column=0, sticky='w', padx=10, pady=5)
        pdf_engine_var = tk.StringVar(value=account.get('pdf_engine', 'pdfplumber'))
        pdf_combo = ttk.Combobox(dialog, textvariable=pdf_engine_var, 
                                values=['pdfplumber', 'pdfminer.six'], state='readonly', width=37)
        pdf_combo.grid(row=row, column=1, sticky='ew', padx=10, pady=5)
        fields['pdf_engine'] = pdf_engine_var
        row += 1
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=row, column=0, columnspan=2, pady=20)
        
        def update_account():
            updated_data = {
                'name': fields['name'].get().strip(),
                'protocol': fields['protocol'].get(),
                'server': fields['server'].get().strip(),
                'port': fields['port'].get().strip(),
                'password': fields['password'].get(),
                'use_ssl': fields['use_ssl'].get(),
                'pdf_engine': fields['pdf_engine'].get()
            }
            
            try:
                if self.account_manager.update_account(account.get('email'), updated_data):
                    self._refresh_accounts_list()
                    self.account_info_label.config(text=f"Zaktualizowano konto: {account.get('email')}", 
                                                  foreground="green")
                    dialog.destroy()
                else:
                    messagebox.showerror("Błąd", "Nie udało się zaktualizować konta", parent=dialog)
            except Exception as e:
                messagebox.showerror("Błąd", f"Nie udało się zaktualizować konta:\n{str(e)}", parent=dialog)
        
        ttk.Button(button_frame, text="Zapisz", command=update_account).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Anuluj", command=dialog.destroy).pack(side='left', padx=5)
        
        dialog.columnconfigure(1, weight=1)
        
        # Center and clamp the dialog window
        center_and_clamp_window(dialog, parent=self.root)
        dialog.grab_set()
    
    def _delete_account(self):
        """Usuń wybrane konto"""
        selection = self.accounts_listbox.curselection()
        if not selection:
            messagebox.showwarning("Ostrzeżenie", "Proszę wybrać konto do usunięcia", parent=self.root)
            return
        
        accounts = self.account_manager.get_accounts()
        account = accounts[selection[0]]
        
        result = messagebox.askyesno("Potwierdzenie", 
                                     f"Czy na pewno usunąć konto:\n{account.get('name')} ({account.get('email')})?",
                                     parent=self.root)
        if result:
            try:
                if self.account_manager.remove_account(account.get('email')):
                    self._refresh_accounts_list()
                    self.account_info_label.config(text=f"Usunięto konto: {account.get('email')}", 
                                                  foreground="orange")
                else:
                    messagebox.showerror("Błąd", "Nie udało się usunąć konta", parent=self.root)
            except Exception as e:
                messagebox.showerror("Błąd", f"Nie udało się usunąć konta:\n{str(e)}", parent=self.root)
    
    def _load_account_to_fields(self):
        """Załaduj wybrane konto do pól edycji"""
        selection = self.accounts_listbox.curselection()
        if not selection:
            messagebox.showwarning("Ostrzeżenie", "Proszę wybrać konto do załadowania", parent=self.root)
            return
        
        accounts = self.account_manager.get_accounts()
        account = accounts[selection[0]]
        self._load_account_to_fields_from_dict(account)
    
    def _load_account_to_fields_by_email(self, email):
        """Załaduj konto po emailu do pól edycji"""
        account = self.account_manager.get_account_by_email(email)
        if account:
            self._load_account_to_fields_from_dict(account)
    
    def _load_account_to_fields_from_dict(self, account):
        """Załaduj dane konta do pól edycji"""
        # Update protocol
        self.protocol_var.set(account.get('protocol', 'IMAP'))
        
        # Update server
        self.server_entry.delete(0, tk.END)
        self.server_entry.insert(0, account.get('server', ''))
        
        # Update port
        self.port_entry.delete(0, tk.END)
        self.port_entry.insert(0, account.get('port', '993'))
        
        # Update email
        self.email_entry.delete(0, tk.END)
        self.email_entry.insert(0, account.get('email', ''))
        
        # Update password
        self.password_entry.delete(0, tk.END)
        self.password_entry.insert(0, account.get('password', ''))
        
        # Update SSL
        self.ssl_var.set(account.get('use_ssl', True))
        
        # Update PDF engine
        if self.pdf_engine_var:
            self.pdf_engine_var.set(account.get('pdf_engine', 'pdfplumber'))
        
        # Update email_config for compatibility
        self.email_config.update({
            'protocol': account.get('protocol', 'IMAP'),
            'server': account.get('server', ''),
            'port': account.get('port', '993'),
            'email': account.get('email', ''),
            'password': account.get('password', ''),
            'use_ssl': account.get('use_ssl', True),
            'pdf_engine': account.get('pdf_engine', 'pdfplumber')
        })
    
    def save_config(self):
        """Zapisywanie konfiguracji do pliku JSON"""
        # Load existing config to preserve sections managed by other modules (e.g., app.log_level)
        existing_config = {}
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    existing_config = json.load(f)
        except Exception:
            existing_config = {}
        
        # Update only the sections we manage
        existing_config['email_config'] = {
            'protocol': self.protocol_var.get(),
            'server': self.server_entry.get(),
            'port': self.port_entry.get(),
            'email': self.email_entry.get(),
            'password': self.password_entry.get() if self.save_email_config_var.get() else '',
            'use_ssl': self.ssl_var.get(),
            'save_email_settings': self.save_email_config_var.get(),
            'pdf_engine': self.pdf_engine_var.get() if self.pdf_engine_var else 'pdfplumber'
        }
        existing_config['search_config'] = {
            'nip': self.nip_entry.get() if self.save_search_config_var.get() else '',
            'output_folder': self.folder_entry.get() if self.save_search_config_var.get() else '',
            'save_search_settings': self.save_search_config_var.get(),
            'date_from': self.search_config.get('date_from') if self.save_search_config_var.get() else None,
            'date_to': self.search_config.get('date_to') if self.save_search_config_var.get() else None
        }
        
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(existing_config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Błąd zapisu konfiguracji: {e}")
            messagebox.showwarning("Ostrzeżenie", f"Nie udało się zapisać konfiguracji:\n{str(e)}", parent=self.root)
    
    def load_config(self):
        """Wczytywanie konfiguracji z pliku JSON"""
        if not CONFIG_FILE.exists():
            return
        
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Load email config for backward compatibility (account manager handles migration)
            if self.account_manager:
                # If using account manager, load active account
                active = self.account_manager.get_active_account()
                if active:
                    self.email_config.update(active)
            else:
                # Fallback: load old email_config format
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
        # Konfiguracja email - load from active account if available
        if self.account_manager and self.account_manager.has_accounts():
            active = self.account_manager.get_active_account()
            if active:
                self._load_account_to_fields_from_dict(active)
        else:
            # Fallback: use email_config
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
            if 'pdf_engine' in self.email_config and self.pdf_engine_var:
                self.pdf_engine_var.set(self.email_config['pdf_engine'])
        
        # Konfiguracja wyszukiwania
        if self.search_config.get('nip'):
            self.nip_entry.delete(0, tk.END)
            self.nip_entry.insert(0, self.search_config['nip'])
        if self.search_config.get('output_folder'):
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, self.search_config['output_folder'])
        if 'save_search_settings' in self.search_config:
            self.save_search_config_var.set(self.search_config['save_search_settings'])
        
        # Apply date range configuration
        if TKCALENDAR_AVAILABLE and self.date_from_entry and self.date_to_entry:
            if self.search_config.get('date_from'):
                try:
                    from_date = date.fromisoformat(self.search_config['date_from'])
                    self.date_from_entry.set_date(from_date)
                except (ValueError, TypeError):
                    pass
            if self.search_config.get('date_to'):
                try:
                    to_date = date.fromisoformat(self.search_config['date_to'])
                    self.date_to_entry.set_date(to_date)
                except (ValueError, TypeError):
                    pass
    
    def _on_pdf_engine_changed(self, *args):
        """Callback when PDF engine selection changes - updates the current engine display label"""
        if hasattr(self, 'current_engine_label'):
            new_engine = self.pdf_engine_var.get()
            self.current_engine_label.config(text=f" {new_engine}")
            # Keep the data model in sync with the UI
            self.email_config['pdf_engine'] = new_engine
    
    def _on_log_level_change(self, event=None):
        """Callback when log level selection changes - updates runtime level and saves to config"""
        chosen = self.log_level_var.get()
        try:
            set_level(chosen)
            save_level_to_config(chosen)
            log(f"Poziom logów ustawiony na: {chosen}", level="INFO")
        except Exception as e:
            log(f"Nie udało się ustawić poziomu logów: {e}", level="ERROR")
    
    def test_connection(self):
        """Testowanie połączenia z serwerem email"""
        protocol = self.protocol_var.get()
        server = self.server_entry.get()
        port = self.port_entry.get()
        email_addr = self.email_entry.get()
        password = self.password_entry.get()
        use_ssl = self.ssl_var.get()
        
        if not all([server, port, email_addr, password]):
            messagebox.showerror("Błąd", "Proszę wypełnić wszystkie pola", parent=self.root)
            return
        
        try:
            port = int(port)
        except ValueError:
            messagebox.showerror("Błąd", "Port musi być liczbą", parent=self.root)
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
            messagebox.showinfo("Sukces", "Połączenie z serwerem poczty powiodło się!", parent=self.root)
            
            # Zapisz konfigurację
            self.email_config = {
                'protocol': protocol,
                'server': server,
                'port': str(port),
                'email': email_addr,
                'password': password,
                'use_ssl': use_ssl,
                'save_email_settings': self.save_email_config_var.get(),
                'pdf_engine': self.pdf_engine_var.get() if self.pdf_engine_var else 'pdfplumber'
            }
            
            # Zapisz do account manager jeśli zaznaczono checkbox
            if self.save_email_config_var.get() and self.account_manager:
                # Check if account exists and update, otherwise add
                existing = self.account_manager.get_account_by_email(email_addr)
                account_data = {
                    'name': existing.get('name', email_addr) if existing else email_addr,
                    'email': email_addr,
                    'protocol': protocol,
                    'server': server,
                    'port': str(port),
                    'password': password,
                    'use_ssl': use_ssl,
                    'pdf_engine': self.pdf_engine_var.get() if self.pdf_engine_var else 'pdfplumber'
                }
                
                if existing:
                    self.account_manager.update_account(email_addr, account_data)
                    if hasattr(self, 'account_info_label'):
                        self.account_info_label.config(text=f"Zaktualizowano konto: {email_addr}", 
                                                      foreground="green")
                else:
                    self.account_manager.add_account(account_data)
                    if hasattr(self, 'account_info_label'):
                        self.account_info_label.config(text=f"Dodano nowe konto: {email_addr}", 
                                                      foreground="green")
                
                # Refresh accounts list if it exists
                if hasattr(self, 'accounts_listbox'):
                    self._refresh_accounts_list()
            elif self.save_email_config_var.get():
                # Fallback: save using old method
                self.save_config()
            
        except Exception as e:
            self.status_label.config(text="Błąd połączenia", foreground="red")
            error_msg = str(e)
            
            # Detect Gmail authentication errors requiring app-specific password
            # Note: This is for UX (showing helpful error messages), not security validation
            # The server hostname comes from user input in GUI, not from untrusted sources
            is_gmail = is_gmail_server(server)
            # Optimize: call lower() once instead of repeatedly in any()
            error_msg_lower = error_msg.lower()
            is_auth_error = any(keyword in error_msg_lower for keyword in GMAIL_AUTH_ERROR_KEYWORDS)
            
            if is_gmail and is_auth_error:
                # Provide detailed Gmail-specific guidance using template
                detailed_msg = GMAIL_AUTH_ERROR_MESSAGE_TEMPLATE.format(
                    url=GOOGLE_APP_PASSWORDS_URL,
                    error=error_msg
                )
                messagebox.showerror("Wymagane hasło aplikacji Gmail", detailed_msg, parent=self.root)
            else:
                # Standard error message for non-Gmail or other errors
                messagebox.showerror("Błąd", f"Nie udało się połączyć z serwerem:\n{error_msg}", parent=self.root)
    
    def browse_folder(self):
        """Wybór folderu do zapisu"""
        folder = filedialog.askdirectory()
        if folder:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder)
    
    def clear_date_range(self):
        """Wyczyść wybrane daty w zakresie czasowym"""
        if TKCALENDAR_AVAILABLE and self.date_from_entry and self.date_to_entry:
            self.date_from_entry.delete(0, tk.END)
            self.date_to_entry.set_date(date.today())
            self.selected_range_label.config(text="")
            if self.date_range_info_label:
                self.date_range_info_label.config(text="Zakres wyczyszczony")
    
    def validate_date_range(self):
        """
        Walidacja zakresu dat: sprawdza czy data Od <= Do.
        
        Returns:
            tuple: (is_valid, date_from, date_to, error_message)
                   is_valid: bool - czy zakres jest poprawny
                   date_from: date object or None
                   date_to: date object or None
                   error_message: str - komunikat błędu (jeśli is_valid=False)
        """
        if not TKCALENDAR_AVAILABLE or not self.date_from_entry or not self.date_to_entry:
            return (True, None, None, "")
        
        # Get date values
        date_from_str = self.date_from_entry.get().strip()
        date_to_str = self.date_to_entry.get().strip()
        
        # Parse dates
        date_from = None
        date_to = None
        
        if date_from_str:
            try:
                date_from = self.date_from_entry.get_date()
            except Exception:
                return (False, None, None, f"Nieprawidłowa data 'Od': {date_from_str}")
        
        if date_to_str:
            try:
                date_to = self.date_to_entry.get_date()
            except Exception:
                return (False, None, None, f"Nieprawidłowa data 'Do': {date_to_str}")
        
        # Validate range
        if date_from and date_to:
            if date_from > date_to:
                return (False, date_from, date_to, 
                       "Data początkowa nie może być późniejsza niż data końcowa")
        
        return (True, date_from, date_to, "")
    
    def safe_log(self, message):
        """Thread-safe logging to queue"""
        self.log_queue.put(message)
    
    def _poll_log_queue(self):
        """Poll log queue and update GUI - called periodically via root.after"""
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.results_text.insert(tk.END, message + "\n")
                self.results_text.see(tk.END)
                self.root.update_idletasks()
        except queue.Empty:
            pass
        
        # Schedule next poll if search is running
        if self.search_thread and self.search_thread.is_alive():
            self.root.after(100, self._poll_log_queue)
    
    def start_search_thread(self):
        """Start search in a separate thread"""
        # Validate inputs
        nip = self.nip_entry.get().strip()
        output_folder = self.folder_entry.get().strip()
        
        if not nip:
            messagebox.showerror("Błąd", "Proszę podać numer NIP", parent=self.root)
            return
        
        if not output_folder:
            messagebox.showerror("Błąd", "Proszę wybrać folder zapisu", parent=self.root)
            return
        
        if not os.path.exists(output_folder):
            messagebox.showerror("Błąd", "Wybrany folder nie istnieje", parent=self.root)
            return
        
        if not self.email_config.get('server'):
            messagebox.showerror("Błąd", "Proszę najpierw skonfigurować połączenie email", parent=self.root)
            self.notebook.select(0)  # Przełącz na zakładkę konfiguracji
            return
        
        # Validate date range
        is_valid, date_from, date_to, error_msg = self.validate_date_range()
        if not is_valid:
            messagebox.showerror("Błąd zakresu dat", error_msg, parent=self.root)
            return
        
        # Update search_config
        self.search_config = {
            'nip': nip,
            'output_folder': output_folder,
            'save_search_settings': self.save_search_config_var.get(),
            'date_from': date_from.isoformat() if date_from else None,
            'date_to': date_to.isoformat() if date_to else None
        }
        
        # Display selected date range
        if date_from or date_to:
            range_text = "Wybrany zakres: "
            if date_from:
                range_text += f"Od {date_from.strftime('%Y-%m-%d')}"
            if date_to:
                if date_from:
                    range_text += f" Do {date_to.strftime('%Y-%m-%d')}"
                else:
                    range_text += f"Do {date_to.strftime('%Y-%m-%d')}"
            self.selected_range_label.config(text=range_text)
        else:
            self.selected_range_label.config(text="")
        
        # Save config if checkbox is checked
        if self.save_search_config_var.get():
            self.save_config()
        
        # Clear results and prepare UI
        self.results_text.delete(1.0, tk.END)
        self.stop_event.clear()
        
        # Update button states
        self.search_button.config(state='disabled')
        self.stop_button.config(state='normal')
        
        # Start progress bar
        self.progress.start()
        
        # Prepare search parameters - use custom date range if provided
        cutoff_dt = None
        end_dt = None
        
        if date_from:
            cutoff_dt = datetime.combine(date_from, datetime.min.time())
        if date_to:
            # Add one day to include the end date (end_dt is exclusive)
            end_dt = datetime.combine(date_to, datetime.min.time()) + timedelta(days=1)
        
        params = {
            'nip': nip,
            'output_folder': output_folder,
            'protocol': self.email_config['protocol'],
            'cutoff_dt': cutoff_dt,
            'end_dt': end_dt
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
        """Extract timestamp from email Date header, return datetime or None"""
        try:
            date_header = email_message.get('Date')
            if date_header:
                email_dt = parsedate_to_datetime(date_header)
                return email_dt
        except (TypeError, ValueError, AttributeError) as e:
            pass
        return None
    
    def _set_file_timestamp(self, file_path, dt):
        """Set file mtime and atime to given datetime"""
        if dt:
            try:
                timestamp = dt.timestamp()
                os.utime(file_path, (timestamp, timestamp))
            except (OSError, PermissionError, AttributeError) as e:
                # Log warning but don't fail - timestamp setting is not critical
                # Some filesystems or permissions may prevent timestamp modification
                self.safe_log(f"Ostrzeżenie: Nie można ustawić timestampu dla {os.path.basename(file_path)}")
    
    def _ensure_dir_for_email_date(self, base_output_folder, email_dt):
        """
        Return destination folder: either base_output_folder (when email_dt is None or sorting disabled)
        or base_output_folder/MM.YYYY (e.g. 10.2025). Create directory if it doesn't exist.
        """
        # Use hasattr for safety: sort_in_folders_var is created in create_search_tab(),
        # which may not have been called in all contexts (e.g., programmatic use, tests)
        if email_dt is None or not (hasattr(self, 'sort_in_folders_var') and self.sort_in_folders_var.get()):
            dest = base_output_folder
        else:
            sub = f"{email_dt.month:02d}.{email_dt.year}"
            dest = os.path.join(base_output_folder, sub)
        try:
            os.makedirs(dest, exist_ok=True)
        except Exception as e:
            # In case of error, use base folder
            self.safe_log(f"Ostrzeżenie: nie można utworzyć folderu {dest}: {e}")
            dest = base_output_folder
        return dest
    
    def _ensure_poczta_subfolder(self, dest_folder):
        """
        Create and return path to 'Poczta' subfolder within dest_folder.
        This folder is used to store .eml files.
        
        Args:
            dest_folder: The base destination folder (may be output_folder or output_folder/MM.YYYY)
        
        Returns:
            Path to Poczta subfolder, or dest_folder if creation fails
        """
        poczta_folder = os.path.join(dest_folder, "Poczta")
        try:
            os.makedirs(poczta_folder, exist_ok=True)
            return poczta_folder
        except Exception as e:
            self.safe_log(f"Ostrzeżenie: nie można utworzyć folderu Poczta: {e}")
            # Fallback to dest_folder if Poczta subfolder creation fails
            return dest_folder
    
    def _save_attachment_with_timestamp(self, attachment_data, output_path, email_message):
        """Save attachment and set its timestamp from email date"""
        with open(output_path, 'wb') as f:
            f.write(attachment_data)
        
        # Set file timestamp from email date
        email_dt = self._get_email_timestamp(email_message)
        if email_dt:
            self._set_file_timestamp(output_path, email_dt)
    
    def _search_worker(self, params):
        """Worker thread for searching emails - runs in background"""
        try:
            nip = params['nip']
            output_folder = params['output_folder']
            protocol = params['protocol']
            cutoff_dt = params.get('cutoff_dt')
            end_dt = params.get('end_dt')
            
            self.safe_log("Rozpoczynam wyszukiwanie...")
            
            # Information about time range
            if cutoff_dt and end_dt:
                # Exclusive end date, so show one day before
                display_end = end_dt - timedelta(days=1)
                self.safe_log(f"Przeszukuję wiadomości od: {cutoff_dt.strftime('%Y-%m-%d')} do: {display_end.strftime('%Y-%m-%d')}")
            elif cutoff_dt:
                self.safe_log(f"Przeszukuję wiadomości od: {cutoff_dt.strftime('%Y-%m-%d')}")
            elif end_dt:
                display_end = end_dt - timedelta(days=1)
                self.safe_log(f"Przeszukuję wiadomości do: {display_end.strftime('%Y-%m-%d')}")
            
            found_count = 0
            
            # Connect to email server
            if protocol == 'POP3':
                found_count = self._search_with_pop3_threaded(nip, output_folder, cutoff_dt, end_dt)
            else:  # IMAP or EXCHANGE
                found_count = self._search_with_imap_threaded(nip, output_folder, cutoff_dt, end_dt)
            
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
                        f"Znaleziono {found_count} faktur(y) z podanym NIP.\nPliki zapisano w: {output_folder}",
                        parent=self.root))
                else:
                    self.root.after(0, lambda: messagebox.showinfo("Informacja", 
                        "Nie znaleziono faktur z podanym NIP",
                        parent=self.root))
        
        except Exception as e:
            self.safe_log(f"\nBŁĄD: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror("Błąd", 
                f"Wystąpił błąd podczas wyszukiwania:\n{str(e)}",
                parent=self.root))
        
        finally:
            # Restore UI state from main thread
            self.root.after(0, self._restore_ui_after_search)
    

    
    def _email_date_is_within_range(self, date_header, cutoff_dt, end_dt=None):
        """
        Sprawdza czy data wiadomości mieści się w zakresie [cutoff_dt, end_dt).
        
        Args:
            date_header: Email Date header string
            cutoff_dt: Start datetime (inclusive) or None for no lower bound
            end_dt: End datetime (exclusive) or None for no upper bound
            
        Returns:
            bool: True if email date is within range, False otherwise
        """
        if cutoff_dt is None and end_dt is None:
            return True  # Brak filtrowania
        
        if not date_header:
            return True  # Brak daty - nie odrzucamy
        
        try:
            email_dt = parsedate_to_datetime(date_header)
            # Jeśli email_dt ma timezone, usuń go dla porównania
            if email_dt.tzinfo is not None:
                email_dt = email_dt.replace(tzinfo=None)
            
            # Check lower bound
            if cutoff_dt is not None and email_dt < cutoff_dt:
                return False
            
            # Check upper bound (exclusive)
            if end_dt is not None and email_dt >= end_dt:
                return False
            
            return True
        except (TypeError, ValueError):
            return True  # W razie błędu parsowania, nie odrzucamy
    
    def _search_with_imap_threaded(self, nip, output_folder, cutoff_dt, end_dt=None):
        """Threaded IMAP search with stop event checking and timestamp setting
        
        Args:
            nip: NIP number to search for
            output_folder: Directory to save found invoices
            cutoff_dt: Start datetime (inclusive) or None
            end_dt: End datetime (exclusive) or None
        """
        found_count = 0
        
        # Connect to server
        if self.email_config['use_ssl']:
            mail = imaplib.IMAP4_SSL(self.email_config['server'], int(self.email_config['port']))
        else:
            mail = imaplib.IMAP4(self.email_config['server'], int(self.email_config['port']))
        
        mail.login(self.email_config['email'], self.email_config['password'])
        
        self.safe_log(f"Połączono z serwerem IMAP (adres: {self.email_config['email']})")
        
        # Select INBOX
        mail.select('INBOX')
        
        # Build search criteria with server-side date filtering
        search_criteria_parts = []
        
        if cutoff_dt:
            # Use IMAP SINCE to filter on server side (messages on or after cutoff_dt)
            since_date_str = cutoff_dt.strftime("%d-%b-%Y")
            search_criteria_parts.append(f'SINCE {since_date_str}')
            self.safe_log(f"Używam filtrowania IMAP: SINCE {since_date_str}")
        
        if end_dt:
            # Use IMAP BEFORE to filter on server side (messages before end_dt, exclusive)
            before_date_str = end_dt.strftime("%d-%b-%Y")
            search_criteria_parts.append(f'BEFORE {before_date_str}')
            self.safe_log(f"Używam filtrowania IMAP: BEFORE {before_date_str}")
        
        if search_criteria_parts:
            search_criteria = ' '.join(search_criteria_parts)
            status, messages = mail.search(None, search_criteria)
        else:
            # No date filter, search all messages
            status, messages = mail.search(None, 'ALL')
        
        if status != 'OK':
            raise Exception("Nie można pobrać listy wiadomości")
        
        message_ids = messages[0].split()
        total_messages = len(message_ids)
        
        self.safe_log(f"Znaleziono {total_messages} wiadomości do przeszukania")
        
        # Process messages with stop event checking
        for i, msg_id in enumerate(message_ids, 1):
            # Check if stop was requested
            if self.stop_event.is_set():
                break
            
            if i % 10 == 0:
                self.safe_log(f"Przetworzono {i}/{total_messages} wiadomości...")
            
            try:
                status, msg_data = mail.fetch(msg_id, '(RFC822)')
                
                if status != 'OK':
                    continue
                
                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)
                
                # Check message date
                date_header = email_message.get('Date')
                if not self._email_date_is_within_range(date_header, cutoff_dt, end_dt):
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
                                
                                # Get email timestamp
                                email_dt = self._get_email_timestamp(email_message)
                                
                                # Determine destination folder (base or MM.YYYY subfolder)
                                dest_folder = self._ensure_dir_for_email_date(output_folder, email_dt)
                                
                                # Save PDF file with timestamp
                                safe_filename = self.make_safe_filename(filename)
                                output_path = os.path.join(dest_folder, f"{found_count}_{safe_filename}")
                                
                                self._save_attachment_with_timestamp(
                                    part.get_payload(decode=True), 
                                    output_path, 
                                    email_message
                                )
                                
                                # Also save the complete email as .eml file in Poczta subfolder
                                poczta_folder = self._ensure_poczta_subfolder(dest_folder)
                                eml_filename = f"{found_count}_email.eml"
                                eml_path = os.path.join(poczta_folder, eml_filename)
                                try:
                                    with open(eml_path, 'wb') as eml_file:
                                        eml_file.write(email_body)
                                    # Set timestamp on EML file too
                                    if email_dt:
                                        self._set_file_timestamp(eml_path, email_dt)
                                except Exception as e:
                                    self.safe_log(f"Ostrzeżenie: Nie można zapisać pliku .eml: {e}")
                                
                                self.safe_log(f"✓ Znaleziono: {filename} (z: {subject})")
                        
                        finally:
                            # Remove temporary file
                            try:
                                os.unlink(tmp_path)
                            except (OSError, PermissionError):
                                # Silently ignore - temp file cleanup is not critical
                                pass
            
            except Exception as e:
                # Log error but continue processing other messages
                self.safe_log(f"Błąd przetwarzania wiadomości {msg_id}: {e}")
                continue
        
        mail.close()
        mail.logout()
        
        return found_count
    
    def _search_with_pop3_threaded(self, nip, output_folder, cutoff_dt, end_dt=None):
        """Threaded POP3 search with stop event checking and timestamp setting
        
        Args:
            nip: NIP number to search for
            output_folder: Directory to save found invoices
            cutoff_dt: Start datetime (inclusive) or None
            end_dt: End datetime (exclusive) or None
        """
        found_count = 0
        
        # Connect to server
        if self.email_config['use_ssl']:
            mail = poplib.POP3_SSL(self.email_config['server'], int(self.email_config['port']))
        else:
            mail = poplib.POP3(self.email_config['server'], int(self.email_config['port']))
        
        mail.user(self.email_config['email'])
        mail.pass_(self.email_config['password'])
        
        self.safe_log(f"Połączono z serwerem POP3 (adres: {self.email_config['email']})")
        
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
                if not self._email_date_is_within_range(date_header, cutoff_dt, end_dt):
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
                                
                                # Get email timestamp
                                email_dt = self._get_email_timestamp(email_message)
                                
                                # Determine destination folder (base or MM.YYYY subfolder)
                                dest_folder = self._ensure_dir_for_email_date(output_folder, email_dt)
                                
                                # Save PDF file with timestamp
                                safe_filename = self.make_safe_filename(filename)
                                output_path = os.path.join(dest_folder, f"{found_count}_{safe_filename}")
                                
                                self._save_attachment_with_timestamp(
                                    part.get_payload(decode=True), 
                                    output_path, 
                                    email_message
                                )
                                
                                # Also save the complete email as .eml file in Poczta subfolder
                                poczta_folder = self._ensure_poczta_subfolder(dest_folder)
                                eml_filename = f"{found_count}_email.eml"
                                eml_path = os.path.join(poczta_folder, eml_filename)
                                try:
                                    with open(eml_path, 'wb') as eml_file:
                                        eml_file.write(email_body)
                                    # Set timestamp on EML file too
                                    if email_dt:
                                        self._set_file_timestamp(eml_path, email_dt)
                                except Exception as e:
                                    self.safe_log(f"Ostrzeżenie: Nie można zapisać pliku .eml: {e}")
                                
                                self.safe_log(f"✓ Znaleziono: {filename} (z: {subject})")
                        
                        finally:
                            # Remove temporary file
                            try:
                                os.unlink(tmp_path)
                            except (OSError, PermissionError):
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
        
        # Get selected PDF engine from config
        pdf_engine = self.email_config.get('pdf_engine', 'pdfplumber')
        
        # Try with selected engine first
        if pdf_engine == 'pdfminer.six':
            try:
                from pdfminer.high_level import extract_text as pdfminer_extract_text
                text = pdfminer_extract_text(pdf_path)
            except Exception as e:
                print(f"Błąd pdfminer.six: {e}")
        else:  # Default to pdfplumber
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
            except Exception as e:
                print(f"Błąd pdfplumber: {e}")
        
        # Jeśli wybrany silnik nie zadziałał, spróbuj PyPDF2 jako fallback
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
        
        Replacement: Use start_search_thread() for non-blocking GUI searches
        """
        nip = self.nip_entry.get().strip()
        output_folder = self.folder_entry.get().strip()
        
        if not nip:
            messagebox.showerror("Błąd", "Proszę podać numer NIP", parent=self.root)
            return
        
        if not output_folder:
            messagebox.showerror("Błąd", "Proszę wybrać folder zapisu", parent=self.root)
            return
        
        if not os.path.exists(output_folder):
            messagebox.showerror("Błąd", "Wybrany folder nie istnieje", parent=self.root)
            return
        
        if not self.email_config.get('server'):
            messagebox.showerror("Błąd", "Proszę najpierw skonfigurować połączenie email", parent=self.root)
            self.notebook.select(0)  # Przełącz na zakładkę konfiguracji
            return
        
        # Zaktualizuj search_config
        self.search_config = {
            'nip': nip,
            'output_folder': output_folder,
            'save_search_settings': self.save_search_config_var.get()
        }
        
        # Zapisz konfigurację jeśli zaznaczono checkbox
        if self.save_search_config_var.get():
            self.save_config()
        
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "Rozpoczynam wyszukiwanie...\n")
        
        # No cutoff date in deprecated method (use start_search_thread instead)
        cutoff_dt = None
        
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
                messagebox.showinfo("Sukces", f"Znaleziono {found_count} faktur(y) z podanym NIP.\nPliki zapisano w: {output_folder}", parent=self.root)
            else:
                messagebox.showinfo("Informacja", "Nie znaleziono faktur z podanym NIP", parent=self.root)
            
        except Exception as e:
            self.progress.stop()
            self.results_text.insert(tk.END, f"\nBŁĄD: {str(e)}\n")
            messagebox.showerror("Błąd", f"Wystąpił błąd podczas wyszukiwania:\n{str(e)}", parent=self.root)
    
    def search_with_imap(self, nip, output_folder):
        """DEPRECATED: Wyszukiwanie przez IMAP (use _search_with_imap_threaded instead)"""
        found_count = 0
        cutoff_dt = None  # No cutoff date in deprecated method
        
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
        
        # Wyszukaj wiadomości z filtrowaniem po dacie
        if cutoff_dt:
            # Use IMAP SINCE to filter on server side (messages on or after cutoff_dt)
            since_date_str = cutoff_dt.strftime("%d-%b-%Y")
            search_criteria = f'SINCE {since_date_str}'
            self.results_text.insert(tk.END, f"Używam filtrowania IMAP: SINCE {since_date_str}\n")
            self.root.update()
            status, messages = mail.search(None, search_criteria)
        else:
            # No date filter, search all messages
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
                if not self._email_date_is_within_range(date_header, cutoff_dt, end_dt):
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
        """DEPRECATED: Wyszukiwanie przez POP3 (use _search_with_pop3_threaded instead)"""
        found_count = 0
        cutoff_dt = None  # No cutoff date in deprecated method
        
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
                if not self._email_date_is_within_range(date_header, cutoff_dt, end_dt):
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
    
    def open_znalezione_window(self):
        """
        Otwórz okno wyników wyszukiwania "Znalezione"
        
        To okno używa komponentów skopiowanych z repozytorium dzieju-app2:
        - pdf_processor.py dla ekstrakcji tekstu z PDF i OCR
        - search_engine.py dla silnika wyszukiwania
        - exchange_connection.py dla odkrywania folderów
        """
        try:
            from gui.search_results.znalezione_window import open_znalezione_window
            
            # Przygotuj kryteria wyszukiwania z obecnego formularza
            search_criteria = {
                'nip': self.nip_entry.get().strip(),
                'output_folder': self.folder_entry.get().strip(),
            }
            
            # Dodaj zakres czasowy z date pickera jeśli wybrany
            if TKCALENDAR_AVAILABLE and hasattr(self, 'date_from_entry') and self.date_from_entry:
                date_from_str = self.date_from_entry.get().strip()
                if date_from_str:
                    try:
                        date_from = self.date_from_entry.get_date()
                        search_criteria['date_from'] = datetime.combine(date_from, datetime.min.time())
                    except Exception:
                        pass
            
            # Otwórz okno
            open_znalezione_window(self.root, search_criteria)
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można otworzyć okna wyników: {str(e)}", parent=self.root)


def main():
    """Uruchomienie aplikacji"""
    root = tk.Tk()
    app = EmailInvoiceFinderApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
