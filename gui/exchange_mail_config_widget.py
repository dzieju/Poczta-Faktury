"""
Exchange-specific mail configuration widget
This is a separate implementation for Exchange mail configuration, completely independent from IMAP configuration.

Source: Copied and adapted from dzieju-app2 repository
Original file: https://github.com/dzieju/dzieju-app2/blob/main/gui/exchange_mail_config_widget.py
"""
import tkinter as tk
from tkinter import ttk, messagebox
import json
import threading
import queue
from pathlib import Path

# Try to import exchangelib
try:
    from exchangelib import Credentials, Account, Configuration, DELEGATE
    HAVE_EXCHANGELIB = True
except ImportError:
    HAVE_EXCHANGELIB = False

# Simple logging function
def log(message, level="INFO"):
    print(f"[{level}] {message}", flush=True)

EXCHANGE_CONFIG_FILE = str(Path.home() / "exchange_mail_config.json")

class ExchangeMailConfigWidget(ttk.Frame):
    """Exchange-only mail configuration widget"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        # Threading support variables
        self.testing_cancelled = False
        self.testing_thread = None
        self.result_queue = queue.Queue()
        
        # Exchange account data
        self.accounts = []
        self.main_account_index = 0
        self.selected_account_index = 0
        
        # Callback for when configuration is saved
        self.on_config_saved = None
        
        self.create_widgets()
        self.load_config()
        
        # Start processing queue
        self._process_result_queue()
    
    def create_widgets(self):
        """Create the UI widgets"""
        # Main container with two columns
        main_frame = ttk.Frame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left side - Account list
        left_frame = ttk.LabelFrame(main_frame, text="Konta Exchange", padding=10)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        # Account listbox with scrollbar
        listbox_frame = ttk.Frame(left_frame)
        listbox_frame.pack(fill="both", expand=True)
        
        self.account_listbox = tk.Listbox(listbox_frame, height=8)
        scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=self.account_listbox.yview)
        self.account_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.account_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.account_listbox.bind("<<ListboxSelect>>", self.on_account_select)
        
        # Account management buttons
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Button(button_frame, text="Dodaj konto", command=self.add_account).pack(side="left", padx=(0, 5))
        ttk.Button(button_frame, text="Usuń konto", command=self.remove_account).pack(side="left", padx=(0, 5))
        ttk.Button(button_frame, text="Ustaw jako główne", command=self.set_main_account).pack(side="left")
        
        # Right side - Account configuration
        right_frame = ttk.LabelFrame(main_frame, text="Konfiguracja konta Exchange", padding=10)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        
        # Configure grid weights
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=2)
        main_frame.grid_rowconfigure(0, weight=1)
        
        # Account configuration form
        self.create_account_form(right_frame)
    
    def create_account_form(self, parent):
        """Create the Exchange account configuration form"""
        # Account name
        ttk.Label(parent, text="Nazwa konta:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.account_name_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.account_name_var, width=40).grid(row=0, column=1, padx=5, pady=5)
        
        # Email
        ttk.Label(parent, text="Adres e-mail:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.email_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.email_var, width=40).grid(row=1, column=1, padx=5, pady=5)
        
        # Username
        ttk.Label(parent, text="Login użytkownika:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.username_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.username_var, width=40).grid(row=2, column=1, padx=5, pady=5)
        
        # Password
        ttk.Label(parent, text="Hasło:").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        self.password_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.password_var, show="*", width=40).grid(row=3, column=1, padx=5, pady=5)
        
        # Exchange server
        ttk.Label(parent, text="Serwer Exchange:").grid(row=4, column=0, sticky="e", padx=5, pady=5)
        self.exchange_server_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.exchange_server_var, width=40).grid(row=4, column=1, padx=5, pady=5)
        
        # Domain (optional)
        ttk.Label(parent, text="Domena (opcjonalnie):").grid(row=5, column=0, sticky="e", padx=5, pady=5)
        self.domain_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.domain_var, width=40).grid(row=5, column=1, padx=5, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=6, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Zapisz ustawienia", command=self.save_config).pack(side="left", padx=5)
        
        self.test_button = ttk.Button(button_frame, text="Testuj połączenie", command=self.toggle_test_connection)
        self.test_button.pack(side="left", padx=5)
        
        self.status_label = ttk.Label(button_frame, text="Gotowy", foreground="green")
        self.status_label.pack(side="left", padx=10)
    
    def add_account(self):
        """Add a new Exchange account"""
        account = {
            "name": "Nowe konto Exchange",
            "email": "",
            "username": "",
            "password": "",
            "exchange_server": "",
            "domain": ""
        }
        self.accounts.append(account)
        self.update_account_list()
        self.account_listbox.selection_clear(0, tk.END)
        self.account_listbox.selection_set(len(self.accounts) - 1)
        self.account_listbox.see(len(self.accounts) - 1)
        self.on_account_select(None)
    
    def remove_account(self):
        """Remove selected account"""
        if not self.accounts:
            messagebox.showwarning("Ostrzeżenie", "Brak kont do usunięcia.")
            return
        
        selection = self.account_listbox.curselection()
        if not selection:
            messagebox.showwarning("Ostrzeżenie", "Wybierz konto do usunięcia.")
            return
        
        idx = selection[0]
        account_name = self.accounts[idx]["name"]
        
        if messagebox.askyesno("Potwierdzenie", f"Czy na pewno usunąć konto '{account_name}'?"):
            del self.accounts[idx]
            
            # Adjust main account index if needed
            if self.main_account_index >= len(self.accounts):
                self.main_account_index = max(0, len(self.accounts) - 1)
            elif self.main_account_index > idx:
                self.main_account_index -= 1
            
            self.update_account_list()
            
            # Select first account if any remain
            if self.accounts:
                self.account_listbox.selection_set(0)
                self.on_account_select(None)
            else:
                self.clear_form()
    
    def set_main_account(self):
        """Set selected account as main account"""
        selection = self.account_listbox.curselection()
        if not selection:
            messagebox.showwarning("Ostrzeżenie", "Wybierz konto do ustawienia jako główne.")
            return
        
        self.main_account_index = selection[0]
        self.update_account_list()
        messagebox.showinfo("Informacja", "Konto główne zostało zmienione.")
    
    def on_account_select(self, event):
        """Handle account selection"""
        selection = self.account_listbox.curselection()
        if not selection:
            return
        
        # Save current form data before switching
        if self.selected_account_index >= 0 and self.selected_account_index < len(self.accounts):
            self.save_form_to_account(self.selected_account_index)
        
        # Load new selection
        self.selected_account_index = selection[0]
        self.load_form_from_account(self.selected_account_index)
    
    def update_account_list(self):
        """Update the account listbox"""
        self.account_listbox.delete(0, tk.END)
        for idx, account in enumerate(self.accounts):
            display_name = account["name"]
            if idx == self.main_account_index:
                display_name += " (główne)"
            self.account_listbox.insert(tk.END, display_name)
    
    def save_form_to_account(self, idx):
        """Save current form data to account at index"""
        if idx < 0 or idx >= len(self.accounts):
            return
        
        account = self.accounts[idx]
        account["name"] = self.account_name_var.get().strip()
        account["email"] = self.email_var.get().strip()
        account["username"] = self.username_var.get().strip()
        account["password"] = self.password_var.get()
        account["exchange_server"] = self.exchange_server_var.get().strip()
        account["domain"] = self.domain_var.get().strip()
    
    def load_form_from_account(self, idx):
        """Load account data to form"""
        if idx < 0 or idx >= len(self.accounts):
            return
        
        account = self.accounts[idx]
        self.account_name_var.set(account.get("name", ""))
        self.email_var.set(account.get("email", ""))
        self.username_var.set(account.get("username", ""))
        self.password_var.set(account.get("password", ""))
        self.exchange_server_var.set(account.get("exchange_server", ""))
        self.domain_var.set(account.get("domain", ""))
    
    def clear_form(self):
        """Clear all form fields"""
        self.account_name_var.set("")
        self.email_var.set("")
        self.username_var.set("")
        self.password_var.set("")
        self.exchange_server_var.set("")
        self.domain_var.set("")
    
    def save_config(self):
        """Save all accounts to config file"""
        if not self.accounts:
            messagebox.showwarning("Ostrzeżenie", "Brak kont do zapisania.")
            return
        
        # Save current form data to selected account
        if self.selected_account_index >= 0 and self.selected_account_index < len(self.accounts):
            # Validation
            if not self.account_name_var.get().strip():
                messagebox.showerror("Błąd", "Nazwa konta nie może być pusta.")
                return
            
            if not self.email_var.get().strip():
                messagebox.showerror("Błąd", "Adres e-mail nie może być pusty.")
                return
            
            self.save_form_to_account(self.selected_account_index)
        
        # Save to file
        try:
            config = {
                "accounts": self.accounts,
                "main_account_index": self.main_account_index
            }
            with open(EXCHANGE_CONFIG_FILE, "w") as f:
                json.dump(config, f, indent=2)
            
            self.update_account_list()
            messagebox.showinfo("Zapisano", "Konfiguracja Exchange została zapisana.")
            log(f"Zapisano konfigurację Exchange: {len(self.accounts)} kont")
            
            # Notify parent of configuration change
            if self.on_config_saved:
                self.on_config_saved()
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można zapisać konfiguracji: {str(e)}")
            log(f"Błąd zapisu konfiguracji Exchange: {e}")
    
    def load_config(self):
        """Load accounts from config file"""
        try:
            with open(EXCHANGE_CONFIG_FILE, "r") as f:
                config = json.load(f)
                self.accounts = config.get("accounts", [])
                self.main_account_index = config.get("main_account_index", 0)
            
            self.update_account_list()
            
            # Select first account if any exist
            if self.accounts:
                self.account_listbox.selection_set(0)
                self.selected_account_index = 0
                self.load_form_from_account(0)
            
            log(f"Załadowano konfigurację Exchange: {len(self.accounts)} kont")
        except FileNotFoundError:
            log("Brak pliku konfiguracji Exchange, tworzę nową konfigurację")
            # Try to migrate from old exchange_config.json
            self.migrate_from_old_config()
        except Exception as e:
            log(f"Błąd ładowania konfiguracji Exchange: {e}")
            messagebox.showerror("Błąd", f"Nie można załadować konfiguracji: {str(e)}")
    
    def migrate_from_old_config(self):
        """Migrate from old exchange_config.json format"""
        try:
            with open("exchange_config.json", "r") as f:
                old_config = json.load(f)
            
            # Create account from old config
            account = {
                "name": f"Exchange ({old_config.get('email', 'Konto')})",
                "email": old_config.get("email", ""),
                "username": old_config.get("username", ""),
                "password": old_config.get("password", ""),
                "exchange_server": old_config.get("server", ""),
                "domain": old_config.get("domain", "")
            }
            
            self.accounts = [account]
            self.main_account_index = 0
            self.update_account_list()
            
            # Select the migrated account
            if self.accounts:
                self.account_listbox.selection_set(0)
                self.selected_account_index = 0
                self.load_form_from_account(0)
            
            log("Zmigrowano konfigurację ze starego formatu exchange_config.json")
            messagebox.showinfo("Migracja", "Konfiguracja została zmigrowana ze starego formatu. Zapisz ją, aby potwierdzić.")
        except FileNotFoundError:
            log("Brak starego pliku konfiguracji do migracji")
        except Exception as e:
            log(f"Błąd migracji starej konfiguracji: {e}")
    
    def toggle_test_connection(self):
        """Toggle between starting and cancelling connection test"""
        if self.testing_thread and self.testing_thread.is_alive():
            self.cancel_test_connection()
        else:
            self.start_test_connection()
    
    def cancel_test_connection(self):
        """Cancel ongoing connection test"""
        self.testing_cancelled = True
        self.status_label.config(text="Anulowanie...", foreground="orange")
        self.test_button.config(text="Testuj połączenie")
    
    def start_test_connection(self):
        """Start the threaded connection test"""
        # Save current form data
        if self.selected_account_index >= 0 and self.selected_account_index < len(self.accounts):
            self.save_form_to_account(self.selected_account_index)
        
        # Get current account data
        if not self.accounts or self.selected_account_index < 0:
            messagebox.showwarning("Ostrzeżenie", "Brak konta do przetestowania.")
            return
        
        account = self.accounts[self.selected_account_index]
        
        # Validate required fields
        if not account.get("email") or not account.get("exchange_server"):
            messagebox.showerror("Błąd", "Wypełnij adres e-mail i serwer Exchange.")
            return
        
        # Reset cancellation flag
        self.testing_cancelled = False
        
        # Update UI
        self.test_button.config(text="Anuluj test")
        self.status_label.config(text="Testowanie połączenia...", foreground="blue")
        
        # Start testing in background thread
        self.testing_thread = threading.Thread(
            target=self._test_exchange_connection,
            args=(account,),
            daemon=True
        )
        self.testing_thread.start()
    
    def _test_exchange_connection(self, account):
        """Test Exchange connection in background thread"""
        try:
            if not HAVE_EXCHANGELIB:
                self.result_queue.put({
                    'type': 'test_error',
                    'error': "Biblioteka exchangelib nie jest zainstalowana. Zainstaluj przez: pip install exchangelib"
                })
                return
                
            if self.testing_cancelled:
                self.result_queue.put({'type': 'test_cancelled'})
                return
            
            # Create credentials
            username = account.get("username", "")
            password = account.get("password", "")
            domain = account.get("domain", "")
            
            if domain:
                username = f"{domain}\\{username}"
            
            creds = Credentials(username=username, password=password)
            config = Configuration(server=account.get("exchange_server"), credentials=creds)
            
            if self.testing_cancelled:
                self.result_queue.put({'type': 'test_cancelled'})
                return
            
            # Test connection
            test_account = Account(
                primary_smtp_address=account.get("email"),
                config=config,
                autodiscover=False,
                access_type=DELEGATE
            )
            
            if self.testing_cancelled:
                self.result_queue.put({'type': 'test_cancelled'})
                return
            
            # Try to access inbox to verify connection
            _ = test_account.inbox.total_count
            
            self.result_queue.put({
                'type': 'test_success',
                'message': f"Połączono z kontem Exchange: {account.get('email')}"
            })
        except Exception as e:
            self.result_queue.put({
                'type': 'test_error',
                'error': f"Błąd połączenia Exchange: {str(e)}"
            })
    
    def _process_result_queue(self):
        """Process results from worker thread"""
        try:
            while True:
                try:
                    result = self.result_queue.get_nowait()
                    
                    if result['type'] == 'test_success':
                        messagebox.showinfo("Połączenie OK", result['message'])
                        self.status_label.config(text="Test połączenia udany", foreground="green")
                        self.test_button.config(text="Testuj połączenie")
                        
                    elif result['type'] == 'test_cancelled':
                        self.status_label.config(text="Test anulowany", foreground="orange")
                        self.test_button.config(text="Testuj połączenie")
                        
                    elif result['type'] == 'test_error':
                        messagebox.showerror("Błąd połączenia", result['error'])
                        self.status_label.config(text="Błąd połączenia", foreground="red")
                        self.test_button.config(text="Testuj połączenie")
                        
                except queue.Empty:
                    break
        except Exception as e:
            log(f"Błąd przetwarzania kolejki wyników: {e}")
        
        # Schedule next check
        self.after(100, self._process_result_queue)
    
    def destroy(self):
        """Cleanup when widget is destroyed"""
        if self.testing_thread and self.testing_thread.is_alive():
            self.testing_cancelled = True
        super().destroy()
