"""
Multi-account mail connection manager supporting both Exchange and IMAP/SMTP

Source: Copied and adapted from dzieju-app2 repository
Original file: https://github.com/dzieju/dzieju-app2/blob/main/gui/mail_search_components/mail_connection.py
"""
import json
import poplib
import email
from pathlib import Path

# Try to import optional libraries
try:
    from imapclient import IMAPClient
    HAVE_IMAPCLIENT = True
except ImportError:
    HAVE_IMAPCLIENT = False

try:
    from exchangelib import Credentials, Account, Configuration, DELEGATE
    HAVE_EXCHANGELIB = True
except ImportError:
    HAVE_EXCHANGELIB = False

# Simple logging function
def log(message, level="INFO"):
    print(f"[{level}] {message}", flush=True)

# Handle optional tkinter import
try:
    from tkinter import messagebox
    HAVE_TKINTER = True
except ImportError:
    HAVE_TKINTER = False
    # Create dummy messagebox for environments without tkinter
    class DummyMessagebox:
        @staticmethod
        def showerror(title, message):
            log(f"ERROR [{title}]: {message}", "ERROR")
        
        @staticmethod
        def showinfo(title, message):
            log(f"INFO [{title}]: {message}", "INFO")
        
        @staticmethod
        def showwarning(title, message):
            log(f"WARNING [{title}]: {message}", "WARNING")
    
    messagebox = DummyMessagebox()

# New multi-account config file
CONFIG_FILE = str(Path.home() / "mail_config.json")
# Legacy Exchange config file for backward compatibility
LEGACY_CONFIG_FILE = str(Path.home() / "exchange_config.json")

# Average message size estimate for folder size calculations (in bytes)
# This is a reasonable middle ground between plain text (~10KB) and 
# messages with attachments (~300KB+)
ESTIMATED_MESSAGE_SIZE = 150 * 1024  # 150KB


class FolderNameMapper:
    """Handles bidirectional mapping between Polish display names and server folder names"""
    
    # Mapping from Polish display names to common server folder names
    POLISH_TO_SERVER = {
        "skrzynka odbiorcza": "INBOX",
        "odebrane": "INBOX",
        "przychodzące": "INBOX",
        "inbox": "INBOX",
        "wysłane": "SENT",
        "wysłano": "SENT",
        "sent items": "SENT",
        "sent": "SENT",
        "robocze": "DRAFTS",
        "szkice": "DRAFTS",
        "drafts": "DRAFTS",
        "wersje robocze": "DRAFTS",
        "spam": "SPAM",
        "junk": "SPAM",
        "junk email": "SPAM",
        "wiadomości-śmieci": "SPAM",
        "śmieci": "TRASH",
        "kosz": "TRASH",
        "trash": "TRASH",
        "deleted items": "TRASH",
        "elementy usunięte": "TRASH",
        "archiwum": "ARCHIVE",
        "archive": "ARCHIVE",
        "ważne": "IMPORTANT",
        "important": "IMPORTANT",
        "oznaczone": "FLAGGED",
        "flagged": "FLAGGED",
        "outbox": "OUTBOX",
        "skrzynka nadawcza": "OUTBOX"
    }
    
    # Manual reverse mapping for display purposes (using preferred Polish names)
    SERVER_TO_POLISH = {
        "INBOX": "skrzynka odbiorcza",
        "SENT": "wysłane",
        "DRAFTS": "robocze",
        "SPAM": "spam",
        "TRASH": "śmieci",
        "ARCHIVE": "archiwum",
        "IMPORTANT": "ważne",
        "FLAGGED": "oznaczone",
        "OUTBOX": "skrzynka nadawcza"
    }
    
    @classmethod
    def polish_to_server(cls, polish_name):
        """Convert Polish folder name to server folder name"""
        if not polish_name:
            return "INBOX"
        
        # First try exact lowercase match
        lower_name = polish_name.lower().strip()
        if lower_name in cls.POLISH_TO_SERVER:
            return cls.POLISH_TO_SERVER[lower_name]
        
        # If no match found, return the original name (it might be a server name already)
        return polish_name
    
    @classmethod
    def server_to_polish(cls, server_name):
        """Convert server folder name to Polish display name"""
        if not server_name:
            return "skrzynka odbiorcza"
        
        # Try exact uppercase match first
        upper_name = server_name.upper()
        if upper_name in cls.SERVER_TO_POLISH:
            return cls.SERVER_TO_POLISH[upper_name]
        
        # If no match found, return the original server name
        return server_name
    
    @classmethod
    def get_folder_display_name(cls, server_name, account_type="imap_smtp"):
        """Get appropriate display name for folder based on account type"""
        # For Exchange, we show actual server names
        # For IMAP/POP, we can show Polish names if available
        if account_type == "exchange":
            return server_name
        else:
            return cls.server_to_polish(server_name)
    
    @classmethod
    def validate_folder_exists(cls, folder_list, target_folder):
        """Check if a target folder exists in the folder list (case-insensitive)"""
        if not folder_list or not target_folder:
            return False
        
        target_lower = target_folder.lower()
        for folder in folder_list:
            if folder.lower() == target_lower:
                return True
        
        # Also check if target is a Polish name that maps to a server folder
        server_name = cls.polish_to_server(target_folder)
        if server_name != target_folder:
            for folder in folder_list:
                if folder.upper() == server_name.upper():
                    return True
        
        return False


class MailConnection:
    """Manages mail server connections for both Exchange and IMAP/SMTP"""
    
    def __init__(self):
        self.account = None
        self.imap_connection = None
        self.pop3_connection = None
        self.current_account_config = None
    
    def load_mail_config(self):
        """Load mail configuration from config file with fallback to legacy"""
        try:
            # Try new format first
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                return config
        except FileNotFoundError:
            # Fallback to legacy Exchange config
            try:
                with open(LEGACY_CONFIG_FILE, "r") as f:
                    legacy_config = json.load(f)
                    # Convert to new format
                    return {
                        "accounts": [{
                            "name": f"Legacy Exchange ({legacy_config.get('email', 'Account')})",
                            "type": "exchange",
                            "email": legacy_config.get("email", ""),
                            "username": legacy_config.get("username", ""),
                            "password": legacy_config.get("password", ""),
                            "auth_method": "password",
                            "exchange_server": legacy_config.get("server", ""),
                            "domain": legacy_config.get("domain", ""),
                            "imap_server": "",
                            "imap_port": 993,
                            "imap_ssl": True,
                            "smtp_server": "",
                            "smtp_port": 587,
                            "smtp_ssl": True,
                            "pop3_server": "",
                            "pop3_port": 995,
                            "pop3_ssl": True,
                            "smtp_server_pop3": "",
                            "smtp_port_pop3": 587,
                            "smtp_ssl_pop3": True
                        }],
                        "main_account_index": 0
                    }
            except FileNotFoundError:
                messagebox.showerror("Błąd konfiguracji", "Brak konfiguracji poczty. Skonfiguruj połączenie w zakładce 'Konfiguracja poczty'.")
                return None
        except Exception as e:
            messagebox.showerror("Błąd konfiguracji", f"Błąd odczytu konfiguracji: {str(e)}")
            return None
    
    def get_main_account(self):
        """Get main account connection"""
        config = self.load_mail_config()
        if not config or not config.get("accounts"):
            return None
        
        main_index = config.get("main_account_index", 0)
        accounts = config.get("accounts", [])
        
        if main_index >= len(accounts):
            main_index = 0
        
        account_config = accounts[main_index]
        return self._get_account_connection(account_config)
    
    def get_account_by_index(self, index):
        """Get account connection by index"""
        config = self.load_mail_config()
        if not config or not config.get("accounts"):
            return None
        
        accounts = config.get("accounts", [])
        if index >= len(accounts):
            return None
        
        account_config = accounts[index]
        return self._get_account_connection(account_config)
    
    def get_imap_account(self):
        """Get first available IMAP/POP3 account connection (excludes Exchange accounts)"""
        config = self.load_mail_config()
        if not config or not config.get("accounts"):
            log("[MAIL CONNECTION] No mail configuration or accounts found")
            return None
        
        accounts = config.get("accounts", [])
        main_index = config.get("main_account_index", 0)
        
        # First, try to use the main account if it's IMAP/POP3
        if main_index < len(accounts):
            main_account = accounts[main_index]
            account_type = main_account.get("type", "exchange")
            if account_type in ["imap_smtp", "pop3_smtp"]:
                log(f"[MAIL CONNECTION] Using main account (index {main_index}) for IMAP: {main_account.get('name', 'Unknown')}")
                return self._get_account_connection(main_account)
        
        # If main account is not IMAP/POP3, find the first IMAP/POP3 account
        for idx, account_config in enumerate(accounts):
            account_type = account_config.get("type", "exchange")
            if account_type in ["imap_smtp", "pop3_smtp"]:
                log(f"[MAIL CONNECTION] Using first available IMAP/POP3 account (index {idx}): {account_config.get('name', 'Unknown')}")
                return self._get_account_connection(account_config)
        
        # No IMAP/POP3 accounts found
        log("[MAIL CONNECTION] No IMAP/POP3 accounts found in configuration")
        return None
    
    def get_folders_with_details(self, account_config):
        """
        Get detailed folder information including SPECIAL-USE flags, message counts, and sizes.
        Uses XLIST if available (Gmail), otherwise LIST with SPECIAL-USE extension.
        
        Returns: List of dicts with keys: name, flags, delimiter, message_count, size
        """
        log("[MAIL CONNECTION] Getting folders with details (SPECIAL-USE/XLIST)")
        
        imap = None
        try:
            # Get IMAP connection
            imap = self._get_imap_connection(account_config)
            if not imap:
                log("[MAIL CONNECTION] ERROR: Could not establish IMAP connection")
                return []
            
            folders_info = []
            
            # Try XLIST first (Gmail extended LIST)
            try:
                log("[MAIL CONNECTION] Attempting XLIST command (Gmail)")
                xlist_folders = imap.xlist_folders()
                folder_list = xlist_folders
                log(f"[MAIL CONNECTION] XLIST successful, got {len(folder_list)} folders")
            except:
                # Fallback to regular LIST
                log("[MAIL CONNECTION] XLIST not supported, using regular LIST")
                folder_list = imap.list_folders()
            
            for folder_data in folder_list:
                if folder_data:
                    try:
                        flags, delimiter, folder_name = folder_data
                        
                        # Decode folder name if bytes
                        if isinstance(folder_name, bytes):
                            folder_name = folder_name.decode('utf-8')
                        
                        folder_name = folder_name.strip()
                        
                        if not folder_name:
                            continue
                        
                        # Get folder status (message count)
                        message_count = 0
                        estimated_size = 0
                        
                        try:
                            # Select folder to get accurate count
                            imap.select_folder(folder_name, readonly=True)
                            
                            # Get folder status
                            status = imap.folder_status(folder_name, ['MESSAGES', 'UIDVALIDITY'])
                            message_count = status.get(b'MESSAGES', 0)
                            
                            # Approximate size (IMAP doesn't provide total size easily)
                            # Use estimated average message size
                            estimated_size = message_count * ESTIMATED_MESSAGE_SIZE
                            
                        except Exception as status_error:
                            log(f"[MAIL CONNECTION] Could not get status for folder '{folder_name}': {status_error}")
                        
                        folder_info = {
                            'name': folder_name,
                            'flags': flags,
                            'delimiter': delimiter if delimiter else '/',
                            'message_count': message_count,
                            'size': estimated_size
                        }
                        
                        folders_info.append(folder_info)
                        log(f"[MAIL CONNECTION] Folder '{folder_name}': {message_count} messages, flags={flags}")
                        
                    except Exception as folder_error:
                        log(f"[MAIL CONNECTION] Error processing folder: {folder_error}")
                        continue
            
            log(f"[MAIL CONNECTION] Successfully retrieved {len(folders_info)} folders with details")
            return folders_info
            
        except Exception as e:
            log(f"[MAIL CONNECTION] ERROR getting folders with details: {str(e)}")
            return []
        finally:
            # Close temporary connection if needed
            if imap and imap != self.imap_connection:
                try:
                    imap.logout()
                    log("[MAIL CONNECTION] Closed temporary IMAP connection")
                except:
                    pass
    
    def load_exchange_mail_config(self):
        """Load Exchange mail configuration from exchange_mail_config.json"""
        try:
            with open("exchange_mail_config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
                return config
        except FileNotFoundError:
            log("[MAIL CONNECTION] No exchange_mail_config.json found")
            return None
        except Exception as e:
            log(f"[MAIL CONNECTION] ERROR loading exchange_mail_config.json: {str(e)}")
            return None
    
    def get_exchange_account(self):
        """Get first available Exchange account connection from exchange_mail_config.json"""
        # Try to load from Exchange-specific config first
        config = self.load_exchange_mail_config()
        
        # If no Exchange-specific config, try to find Exchange account in mail_config.json
        if not config:
            log("[MAIL CONNECTION] No Exchange-specific config found, checking mail_config.json")
            config = self.load_mail_config()
        
        if not config or not config.get("accounts"):
            log("[MAIL CONNECTION] No Exchange configuration or accounts found")
            return None
        
        accounts = config.get("accounts", [])
        main_index = config.get("main_account_index", 0)
        
        # First, try to use the main account if it's Exchange
        if main_index < len(accounts):
            main_account = accounts[main_index]
            # In exchange_mail_config.json, all accounts are Exchange, no type field needed
            # But check for type field if it exists (for mail_config.json compatibility)
            account_type = main_account.get("type", "exchange")
            if account_type == "exchange":
                log(f"[MAIL CONNECTION] Using main Exchange account (index {main_index}): {main_account.get('name', 'Unknown')}")
                # Add type field if missing (for exchange_mail_config.json accounts)
                if "type" not in main_account:
                    main_account["type"] = "exchange"
                return self._get_account_connection(main_account)
        
        # If main account is not Exchange, find the first Exchange account
        for idx, account_config in enumerate(accounts):
            account_type = account_config.get("type", "exchange")
            if account_type == "exchange":
                log(f"[MAIL CONNECTION] Using first available Exchange account (index {idx}): {account_config.get('name', 'Unknown')}")
                # Add type field if missing (for exchange_mail_config.json accounts)
                if "type" not in account_config:
                    account_config["type"] = "exchange"
                return self._get_account_connection(account_config)
        
        # No Exchange accounts found
        log("[MAIL CONNECTION] No Exchange accounts found in configuration")
        return None
    
    def _get_account_connection(self, account_config):
        """Get connection for specific account configuration"""
        # Close any existing connections before creating new ones
        self.close_connections()
        
        self.current_account_config = account_config
        account_type = account_config.get("type", "exchange")
        account_name = account_config.get("name", "Unknown Account")
        account_email = account_config.get("email", "Unknown Email")
        
        log(f"[MAIL CONNECTION] Connecting to account: '{account_name}' ({account_email})")
        log(f"[MAIL CONNECTION] Account type: {account_type}")
        
        # Log account configuration details (without sensitive data)
        if account_type == "exchange":
            server = account_config.get("exchange_server", "")
            domain = account_config.get("domain", "")
            log(f"[MAIL CONNECTION] Exchange server: {server}, domain: {domain}")
        elif account_type == "imap_smtp":
            imap_server = account_config.get("imap_server", "")
            smtp_server = account_config.get("smtp_server", "")
            log(f"[MAIL CONNECTION] IMAP server: {imap_server}, SMTP server: {smtp_server}")
        elif account_type == "pop3_smtp":
            pop3_server = account_config.get("pop3_server", "")
            smtp_server = account_config.get("smtp_server_pop3", "")
            log(f"[MAIL CONNECTION] POP3 server: {pop3_server}, SMTP server: {smtp_server}")
        
        try:
            if account_type == "exchange":
                return self._get_exchange_connection(account_config)
            elif account_type == "imap_smtp":
                return self._get_imap_connection(account_config)
            elif account_type == "pop3_smtp":
                return self._get_pop3_connection(account_config)
            else:
                log(f"[MAIL CONNECTION] WARNING: Unknown account type '{account_type}', defaulting to IMAP")
                # Default to IMAP for backward compatibility
                return self._get_imap_connection(account_config)
        except Exception as e:
            log(f"[MAIL CONNECTION] Connection failed for account '{account_name}' ({account_type}): {str(e)}")
            messagebox.showerror("Błąd połączenia", f"Nie można połączyć z kontem poczty: {str(e)}")
            return None
    
    def _get_exchange_connection(self, account_config):
        """Get Exchange connection"""
        if not HAVE_EXCHANGELIB:
            raise ImportError("exchangelib library not installed. Install with: pip install exchangelib")
        
        creds = Credentials(
            username=account_config.get("username", ""),
            password=account_config.get("password", "")
        )
        config = Configuration(
            server=account_config.get("exchange_server", ""),
            credentials=creds
        )
        account = Account(
            primary_smtp_address=account_config.get("email", ""),
            config=config,
            autodiscover=False,
            access_type=DELEGATE
        )
        self.account = account
        return account
    
    def _get_imap_connection(self, account_config):
        """Get IMAP connection"""
        if not HAVE_IMAPCLIENT:
            raise ImportError("imapclient library not installed. Install with: pip install imapclient")
        
        imap = IMAPClient(
            account_config.get("imap_server", ""),
            port=account_config.get("imap_port", 993),
            ssl=account_config.get("imap_ssl", True)
        )
        
        imap.login(
            account_config.get("username", ""),
            account_config.get("password", "")
        )
        self.imap_connection = imap
        return imap
    
    def _get_pop3_connection(self, account_config):
        """Get POP3 connection"""
        if account_config.get("pop3_ssl", True):
            pop3 = poplib.POP3_SSL(
                account_config.get("pop3_server", ""),
                account_config.get("pop3_port", 995)
            )
        else:
            pop3 = poplib.POP3(
                account_config.get("pop3_server", ""),
                account_config.get("pop3_port", 995)
            )
        
        pop3.user(account_config.get("username", ""))
        pop3.pass_(account_config.get("password", ""))
        self.pop3_connection = pop3
        return pop3
    
    def get_folder_by_path(self, account, folder_path):
        """Get folder by path - works for Exchange, IMAP, and POP3"""
        if not self.current_account_config:
            log("[MAIL CONNECTION] ERROR: No account configuration available for get_folder_by_path")
            return None
        
        account_type = self.current_account_config.get("type", "unknown")
        log(f"[MAIL CONNECTION] Getting folder by path for account type: {account_type}, path: {folder_path}")
        
        if account_type == "exchange":
            return self._get_exchange_folder_by_path(account, folder_path)
        elif account_type == "pop3_smtp":
            return self._get_pop3_folder_by_path(account, folder_path)
        elif account_type == "imap_smtp":
            return self._get_imap_folder_by_path(account, folder_path)
        else:
            log(f"[MAIL CONNECTION] WARNING: Unknown account type '{account_type}', defaulting to IMAP folder behavior")
            return self._get_imap_folder_by_path(account, folder_path)
    
    def _get_exchange_folder_by_path(self, account, folder_path):
        """Get Exchange folder by path"""
        try:
            path_parts = folder_path.split("/")
            current_folder = account.inbox
            
            # Check if the first part is a known Polish inbox name
            first_part_mapped = FolderNameMapper.polish_to_server(path_parts[0] if path_parts else "")
            if first_part_mapped == "INBOX" or path_parts[0].lower() in ["inbox", "skrzynka odbiorcza"]:
                path_parts = path_parts[1:]  # Skip inbox part
            
            for part in path_parts:
                if part:
                    found = False
                    for child in current_folder.children:
                        if child.name.lower() == part.lower():
                            current_folder = child
                            found = True
                            break
                    if not found:
                        log(f"Nie znaleziono folderu: {part} w ścieżce {folder_path}")
                        return account.inbox
            
            return current_folder
        except Exception as e:
            messagebox.showerror("Błąd folderu", f"Błąd dostępu do folderu: {str(e)}")
            return account.inbox
    
    def _get_imap_folder_by_path(self, imap, folder_path):
        """Get IMAP folder by path"""
        try:
            # Use the new FolderNameMapper for consistent translation
            folder_name = FolderNameMapper.polish_to_server(folder_path)
            log(f"[MAIL CONNECTION] Mapping folder path '{folder_path}' to server name '{folder_name}'")
            
            # Select the folder
            try:
                imap.select_folder(folder_name)
                return folder_name
            except:
                # Fallback to INBOX
                imap.select_folder("INBOX")
                return "INBOX"
                
        except Exception as e:
            log(f"Błąd dostępu do folderu IMAP {folder_path}: {str(e)}")
            imap.select_folder("INBOX")
            return "INBOX"
    
    def _get_pop3_folder_by_path(self, pop3, folder_path):
        """Get POP3 folder by path - POP3 only supports inbox"""
        # POP3 only supports the main mailbox (inbox)
        # All folder paths are treated as the main mailbox
        return "INBOX"
    
    def get_folder_with_subfolders(self, account, folder_path, excluded_folders=None):
        """Get folder and all its subfolders recursively"""
        if not self.current_account_config:
            log("[MAIL CONNECTION] ERROR: No account configuration available for get_folder_with_subfolders")
            return []
        
        account_type = self.current_account_config.get("type", "unknown")
        log(f"[MAIL CONNECTION] Getting folder with subfolders for account type: {account_type}, path: {folder_path}")
        
        if account_type == "exchange":
            return self._get_exchange_folder_with_subfolders(account, folder_path, excluded_folders)
        elif account_type == "pop3_smtp":
            log("[MAIL CONNECTION] POP3 only supports single mailbox")
            # For POP3, this is simplified as POP3 only has one mailbox
            return ["INBOX"]
        elif account_type == "imap_smtp":
            log("[MAIL CONNECTION] IMAP simplified folder handling")
            # For IMAP, this is simplified as most IMAP operations work on single folders
            folder = self.get_folder_by_path(account, folder_path)
            return [folder] if folder else []
        else:
            log(f"[MAIL CONNECTION] WARNING: Unknown account type '{account_type}', defaulting to IMAP behavior")
            folder = self.get_folder_by_path(account, folder_path)
            return [folder] if folder else []
    
    def _get_exchange_folder_with_subfolders(self, account, folder_path, excluded_folders=None):
        """Get Exchange folder and all its subfolders recursively
        
        Note: This method now searches ALL folders starting from root, not just subfolders
        of the specified folder_path. This ensures complete Exchange mailbox search.
        The folder_path parameter is kept for backward compatibility but is no longer
        used to limit the search scope.
        """
        try:
            # Start from root folder to search ALL Exchange folders, not just subfolders
            # of the specified path. This ensures complete mailbox coverage.
            log(f"[MAIL CONNECTION] Starting Exchange folder search from root (ignoring folder_path parameter '{folder_path}' for complete coverage)")
            
            try:
                root_folder = account.root
                log(f"[MAIL CONNECTION] Successfully accessed root folder: '{root_folder.name}'")
            except Exception as root_error:
                log(f"[MAIL CONNECTION] Could not access root folder, trying inbox parent: {root_error}")
                try:
                    root_folder = account.inbox.parent
                    log(f"[MAIL CONNECTION] Using inbox parent: '{root_folder.name}'")
                except Exception as parent_error:
                    log(f"[MAIL CONNECTION] Could not access inbox parent, falling back to inbox: {parent_error}")
                    root_folder = account.inbox
                    log(f"[MAIL CONNECTION] Using inbox as fallback: '{root_folder.name}'")
            
            # Parse excluded folders
            excluded_names = set()
            if excluded_folders:
                if isinstance(excluded_folders, str):
                    # Parse comma-separated string
                    excluded_names = set(f.strip() for f in excluded_folders.split(',') if f.strip())
                elif isinstance(excluded_folders, (list, set)):
                    excluded_names = set(excluded_folders)
                
                if excluded_names:
                    log(f"[MAIL CONNECTION] Excluding {len(excluded_names)} folders: {', '.join(excluded_names)}")
            
            # Get all subfolders recursively from root (this covers entire mailbox)
            all_folders = self._get_all_subfolders_recursive(root_folder, excluded_names)
            
            # Include root folder itself if it's not excluded
            if root_folder.name not in excluded_names:
                all_folders.insert(0, root_folder)
            
            # Also ensure well-known folders are included (inbox, sent, drafts, etc.)
            well_known_folders = []
            try:
                if hasattr(account, 'inbox') and account.inbox:
                    well_known_folders.append(account.inbox)
                if hasattr(account, 'sent') and account.sent:
                    well_known_folders.append(account.sent)
                if hasattr(account, 'drafts') and account.drafts:
                    well_known_folders.append(account.drafts)
                if hasattr(account, 'trash') and account.trash:
                    well_known_folders.append(account.trash)
                if hasattr(account, 'junk') and account.junk:
                    well_known_folders.append(account.junk)
                
                # Add well-known folders if not already in list and not excluded
                for wk_folder in well_known_folders:
                    if wk_folder and wk_folder.name not in excluded_names:
                        if not any(f.name == wk_folder.name for f in all_folders):
                            all_folders.append(wk_folder)
                            log(f"[MAIL CONNECTION] Added well-known folder: {wk_folder.name}")
            except Exception as wk_error:
                log(f"[MAIL CONNECTION] Warning: Could not access well-known folders: {wk_error}")
            
            log(f"[MAIL CONNECTION] Exchange folder search complete: {len(all_folders)} folders to search")
            log(f"[MAIL CONNECTION] Folders include: {', '.join([f.name for f in all_folders[:10]])}{'...' if len(all_folders) > 10 else ''}")
            
            return all_folders
            
        except Exception as e:
            log(f"[MAIL CONNECTION] ERROR getting Exchange folders for search: {str(e)}")
            messagebox.showerror("Błąd folderów", f"Błąd pobierania listy folderów: {str(e)}")
            return []
    
    def _get_all_subfolders_recursive(self, folder, excluded_folder_names=None):
        """Recursively get all subfolders of a given folder"""
        if excluded_folder_names is None:
            excluded_folder_names = set()
        
        subfolders = []
        try:
            # Access children - may trigger network call to Exchange server
            children = folder.children
            log(f"[MAIL CONNECTION] Accessing {len(children)} children of folder '{folder.name}'")
            
            for child in children:
                if child.name not in excluded_folder_names:
                    subfolders.append(child)
                    # Recursively get subfolders
                    nested_subfolders = self._get_all_subfolders_recursive(child, excluded_folder_names)
                    subfolders.extend(nested_subfolders)
                else:
                    log(f"Wykluczono folder: {child.name}")
        except Exception as e:
            log(f"[MAIL CONNECTION] ERROR accessing subfolders of '{folder.name}': {str(e)}")
            # Continue with what we have so far instead of failing completely
        
        return subfolders
    
    def _validate_account_config_for_folder_discovery(self, account_type):
        """Validate that account configuration is complete for folder discovery"""
        if not self.current_account_config:
            return False
        
        config = self.current_account_config
        
        # Basic validation for all account types
        required_basic = ["email", "username", "password"]
        for field in required_basic:
            if not config.get(field):
                log(f"[MAIL CONNECTION] Missing required field '{field}' for account type {account_type}")
                return False
        
        # Type-specific validation
        if account_type == "exchange":
            required_exchange = ["exchange_server", "domain"]
            for field in required_exchange:
                if not config.get(field):
                    log(f"[MAIL CONNECTION] Missing Exchange field '{field}'")
                    return False
        elif account_type == "imap_smtp":
            required_imap = ["imap_server", "smtp_server"]
            for field in required_imap:
                if not config.get(field):
                    log(f"[MAIL CONNECTION] Missing IMAP/SMTP field '{field}'")
                    return False
        elif account_type == "pop3_smtp":
            required_pop3 = ["pop3_server", "smtp_server_pop3"]
            for field in required_pop3:
                if not config.get(field):
                    log(f"[MAIL CONNECTION] Missing POP3/SMTP field '{field}'")
                    return False
        
        log(f"[MAIL CONNECTION] Account configuration validation passed for type: {account_type}")
        return True

    def get_available_folders_for_exclusion(self, account, folder_path):
        """Get list of available folders that can be excluded from search"""
        # Enhanced validation and logging
        if not self.current_account_config:
            log("[MAIL CONNECTION] ERROR: No account configuration available for folder discovery")
            log("[MAIL CONNECTION] Account must be configured before calling this method")
            # Return fallback folders instead of trying to load wrong account type
            return self._get_fallback_folders()
        
        account_type = self.current_account_config.get("type", "unknown")
        account_name = self.current_account_config.get("name", "Unknown Account")
        
        log(f"[MAIL CONNECTION] Getting available folders for account: '{account_name}' (type: {account_type})")
        log(f"[MAIL CONNECTION] Folder path: {folder_path}")
        
        # Validate account configuration before proceeding
        if not self._validate_account_config_for_folder_discovery(account_type):
            log(f"[MAIL CONNECTION] ERROR: Invalid or incomplete configuration for account type: {account_type}")
            # Return fallback folders for GUI to show something useful
            return self._get_fallback_folders()
        
        try:
            if account_type == "exchange":
                log("[MAIL CONNECTION] Using Exchange folder detection")
                return self._get_exchange_available_folders(account, folder_path)
            elif account_type == "pop3_smtp":
                log("[MAIL CONNECTION] Using POP3 folder detection")
                # For POP3, only INBOX is available
                return ["INBOX"]
            elif account_type == "imap_smtp":
                log("[MAIL CONNECTION] Using IMAP folder detection")
                return self._get_imap_available_folders(folder_path)
            else:
                log(f"[MAIL CONNECTION] WARNING: Unknown account type '{account_type}', defaulting to IMAP folder detection")
                return self._get_imap_available_folders(folder_path)
        except Exception as e:
            log(f"[MAIL CONNECTION] ERROR during folder discovery: {str(e)}")
            # Provide fallback folders when discovery fails
            return self._get_fallback_folders()
    
    def _get_exchange_available_folders(self, account, folder_path):
        """Get available Exchange folders for exclusion"""
        try:
            # Start from root folder to discover ALL folders, not just subfolders of specified path
            # This ensures system folders (Sent Items, Drafts, etc.) are included
            try:
                root_folder = account.root
                log(f"[MAIL CONNECTION] Starting Exchange folder discovery from root: '{root_folder.name}'")
            except Exception as root_error:
                log(f"[MAIL CONNECTION] Could not access root folder, using inbox parent: {root_error}")
                try:
                    root_folder = account.inbox.parent
                    log(f"[MAIL CONNECTION] Using inbox parent: '{root_folder.name}'")
                except Exception as parent_error:
                    log(f"[MAIL CONNECTION] Could not access inbox parent, falling back to specified path: {parent_error}")
                    root_folder = self.get_folder_by_path(account, folder_path)
                    if not root_folder:
                        log("[MAIL CONNECTION] ERROR: Could not access any folder for discovery")
                        return self._get_fallback_folders()
            
            # Get all subfolders recursively (without exclusions since we want to show all as options)
            all_subfolders = self._get_all_subfolders_recursive(root_folder, set())
            
            # Extract folder names from folder objects
            folder_names = [subfolder.name for subfolder in all_subfolders]
            folder_names.sort()  # Sort alphabetically for better UX
            
            # Add common Exchange folders if not found
            exchange_common = ["Sent Items", "Drafts", "Deleted Items", "Junk Email", "Outbox"]
            for common_folder in exchange_common:
                if common_folder not in folder_names:
                    folder_names.append(common_folder)
            
            log(f"[MAIL CONNECTION] Found Exchange folders for exclusion ({len(folder_names)}):")
            for i, name in enumerate(folder_names, 1):
                log(f"  {i}. {name}")
            
            return folder_names
            
        except Exception as e:
            log(f"[MAIL CONNECTION] ERROR getting Exchange folders for exclusion: {str(e)}")
            return self._get_fallback_folders()
    
    def _get_imap_available_folders(self, folder_path):
        """Get available IMAP folders for exclusion by connecting to server"""
        imap = None
        try:
            if not self.current_account_config:
                log("[MAIL CONNECTION] ERROR: No account configuration available for IMAP folder discovery")
                return self._get_fallback_folders()
            
            # Get IMAP connection
            imap = self._get_imap_connection(self.current_account_config)
            if not imap:
                log("[MAIL CONNECTION] ERROR: Could not establish IMAP connection for folder discovery")
                return self._get_fallback_folders()
            
            # List all folders on the server
            folders = imap.list_folders()
            
            # Pre-compute the normalized folder path to avoid repeated calls in loop
            folder_path_normalized = FolderNameMapper.polish_to_server(folder_path)
            
            folder_names = []
            for folder_info in folders:
                if folder_info:
                    try:
                        # IMAPClient returns tuple (flags, delimiter, folder_name)
                        flags, delimiter, folder_name = folder_info
                        
                        log(f"[MAIL CONNECTION] Found folder: {folder_name}")
                        
                        # Clean up folder name and decode if bytes
                        if isinstance(folder_name, bytes):
                            folder_name = folder_name.decode('utf-8')
                        
                        folder_name = folder_name.strip()
                        
                        # Skip empty names and the current folder path to avoid self-exclusion  
                        if folder_name and folder_name not in [folder_path, folder_path_normalized]:
                            folder_names.append(folder_name)
                            log(f"[MAIL CONNECTION] Added folder: {folder_name}")
                        
                    except Exception as folder_parse_error:
                        log(f"[MAIL CONNECTION] ERROR parsing folder: {folder_info}, error: {folder_parse_error}")
                        continue
            
            # Always include common folders even if not found on server
            common_folders = ["SENT", "Sent", "DRAFTS", "Drafts", "SPAM", "Junk", "TRASH", "Trash", "Deleted"]
            for common_folder in common_folders:
                if common_folder not in folder_names:
                    folder_names.append(common_folder)
            
            # Remove duplicates while preserving order
            unique_folders = []
            seen = set()
            for folder in folder_names:
                if folder.lower() not in seen:
                    unique_folders.append(folder)
                    seen.add(folder.lower())
            
            log(f"[MAIL CONNECTION] Found {len(unique_folders)} IMAP folders: {unique_folders}")
            return unique_folders
            
        except Exception as e:
            log(f"[MAIL CONNECTION] ERROR getting IMAP folders: {str(e)}")
            # Return fallback list
            return self._get_fallback_folders()
        finally:
            # Always clean up the temporary IMAP connection used for folder discovery
            if imap and imap != self.imap_connection:
                try:
                    imap.logout()
                    log("[MAIL CONNECTION] Closed temporary IMAP connection for folder discovery")
                except:
                    pass
    
    def _get_fallback_folders(self):
        """Get fallback folder list when discovery fails"""
        return ["SENT", "Sent", "DRAFTS", "Drafts", "SPAM", "Junk", "TRASH", "Trash", "Deleted"]
    
    def close_connections(self):
        """Close all active connections"""
        log("[MAIL CONNECTION] Closing all connections")
        
        if self.imap_connection:
            try:
                self.imap_connection.logout()
                log("[MAIL CONNECTION] IMAP connection closed")
            except:
                pass
            self.imap_connection = None
        
        if self.pop3_connection:
            try:
                self.pop3_connection.quit()
                log("[MAIL CONNECTION] POP3 connection closed")
            except:
                pass
            self.pop3_connection = None
        
        self.account = None
        if self.current_account_config:
            account_name = self.current_account_config.get("name", "Unknown")
            log(f"[MAIL CONNECTION] Cleared account configuration for: {account_name}")
        self.current_account_config = None
    
    def get_current_account_info(self):
        """Get information about the currently configured account (for debugging)"""
        if not self.current_account_config:
            return "No account configured"
        
        account_type = self.current_account_config.get("type", "unknown")
        account_name = self.current_account_config.get("name", "Unknown")
        account_email = self.current_account_config.get("email", "Unknown")
        
        return f"Account: '{account_name}' ({account_email}) - Type: {account_type}"
    
    def get_account_and_folder_info(self, current_folder_path=None):
        """Get combined information about current account and active folder"""
        if not self.current_account_config:
            return "Konto: Nieskonfigurowane", "Folder: Brak konfiguracji"
        
        account_type = self.current_account_config.get("type", "unknown")
        account_name = self.current_account_config.get("name", "Nieznane")
        account_email = self.current_account_config.get("email", "")
        
        # Format account info with more details
        if account_type == "exchange":
            server = self.current_account_config.get("exchange_server", "")
            account_info = f"Exchange: {account_name} ({account_email}) @ {server}"
        elif account_type == "imap_smtp":
            server = self.current_account_config.get("imap_server", "")
            account_info = f"IMAP: {account_name} ({account_email}) @ {server}"
        elif account_type == "pop3_smtp":
            server = self.current_account_config.get("pop3_server", "")
            account_info = f"POP3: {account_name} ({account_email}) @ {server}"
        else:
            account_info = f"Nieznany typ: {account_name} ({account_email})"
        
        # Format folder info with validation
        if current_folder_path:
            # Show both the user input and what it maps to for server
            if account_type == "exchange":
                folder_info = f"Folder: {current_folder_path}"
            else:
                # For IMAP/POP, show the mapping and validation
                server_folder = FolderNameMapper.polish_to_server(current_folder_path)
                if server_folder != current_folder_path:
                    folder_info = f"Folder: {current_folder_path} → {server_folder}"
                else:
                    folder_info = f"Folder: {current_folder_path}"
                
                # Add validation info if we can check folder existence
                try:
                    # Try to get a list of folders to validate against
                    available_folders = self.get_available_folders_for_exclusion(
                        self.account or self.imap_connection or self.pop3_connection, 
                        current_folder_path
                    )
                    if available_folders and len(available_folders) > 1:  # More than just fallback
                        if FolderNameMapper.validate_folder_exists(available_folders, current_folder_path):
                            folder_info += " ✓"
                        else:
                            folder_info += " ⚠"
                except:
                    pass  # Don't show validation if we can't check
        else:
            folder_info = "Folder: Brak"
        
        return account_info, folder_info