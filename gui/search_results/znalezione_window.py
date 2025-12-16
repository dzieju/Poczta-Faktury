"""
Znalezione (Found) - Search Results Window

This window displays search results from email searches, including:
- Results table with columns (date, sender, subject, folder, attachments, status)
- PDF snippet display showing matched text from attachments
- Action buttons (Open Attachment, Show in Mail)
- Pagination support

Source: Created for Poczta-Faktury based on design from dzieju-app2
Layout inspiration: https://github.com/dzieju/dzieju-app2/blob/fcee6b91bf240d17ceb38f8564beab5aa9637437/imap_tab_visual_mockup.html
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
import os
import subprocess
import sys
import re
import email
from email.header import decode_header
import json
from pathlib import Path

# Import logger from our local gui module
try:
    from gui.logger import log
except ImportError:
    def log(message, level="INFO"):
        print(f"[{level}] {message}", flush=True)

try:
    from gui.imap_search_components.search_engine import EmailSearchEngine, search_messages
except ImportError:
    log("Warning: EmailSearchEngine not available")
    EmailSearchEngine = None
    search_messages = None

# Placeholder text for demonstration window
PLACEHOLDER_TEXT = """To jest okno wyników wyszukiwania \"Znalezione\".

W pełnej implementacji tutaj będą wyświetlane:
- Wiadomości email znalezione w wyszukiwaniu
- Dopasowania NIP w załącznikach PDF
- Fragmenty tekstu z PDF pokazujące kontekst dopasowania

Komponenty zostały skopiowane z repozytorium dzieju-app2:
- pdf_processor.py (ekstrakcja tekstu i OCR)
- search_engine.py (silnik wyszukiwania)
- exchange_connection.py (odkrywanie folderów)

Aby w pełni zintegrować tę funkcjonalność, należy:
1. Podłączyć istniejące połączenie email z aplikacji
2. Przekazać kryteria wyszukiwania (NIP, zakres dat)
3. Wywołać search_messages() z odpowiednimi parametrami"""


class ZnalezioneWindow:
    """
    Window for displaying search results
    
    This window shows email search results in a table format with support for:
    - Displaying message metadata (date, sender, subject, folder, attachments)
    - Showing PDF snippet matches when a message is selected
    - Action buttons for interacting with messages
    - Pagination for large result sets
    """
    
    def __init__(self, parent, search_criteria=None):
        """
        Initialize the Znalezione (Found) window
        
        Args:
            parent: Parent Tkinter widget
            search_criteria: dict with search parameters to execute
        """
        self.parent = parent
        self.search_criteria = search_criteria or {}
        
        # Cache for PDF extraction results to avoid re-running OCR
        self.pdf_cache = {}
        
        # Current results
        self.results = {
            'messages': [],
            'message_to_folder_map': {},
            'matches': {},
            'folder_results': {},
            'total_count': 0
        }
        
        # Pagination state
        self.current_page = 0
        self.per_page = 50
        
        # Metadata storage for tree items
        self.item_metadata = {}
        
        # Config file path
        self.config_file = Path.home() / '.poczta_faktury_config.json'
        
        # Create window
        self.window = tk.Toplevel(parent)
        self.window.title("Znalezione - Wyniki wyszukiwania")
        self.window.geometry("1000x700")
        
        # Create UI
        self.create_widgets()
        
        # If search criteria provided, start search automatically
        if self.search_criteria:
            self.start_search()
        
        log("ZnalezioneWindow initialized")
    
    def _get_pdf_engine_from_config(self):
        """
        Read the PDF engine setting from config file.
        
        Returns:
            str: PDF engine name ('pdfplumber' or 'pdfminer.six'), defaults to 'pdfplumber'
        """
        default_engine = 'pdfplumber'
        
        # Try to read from config file
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                    # Try email_config.pdf_engine first (new format)
                    engine = config.get('email_config', {}).get('pdf_engine')
                    if engine:
                        return engine
                    
                    # Fall back to top-level pdf_engine (alternative format)
                    engine = config.get('pdf_engine')
                    if engine:
                        return engine
        except Exception as e:
            # Log but don't fail - just use default
            log(f"Could not read PDF engine from config: {e}", level="WARNING")
        
        return default_engine
    
    def create_widgets(self):
        """Create the UI components"""
        # Top frame with search info and actions
        top_frame = ttk.Frame(self.window, padding=10)
        top_frame.pack(fill='x', side='top')
        
        # Search criteria label
        self.search_info_label = ttk.Label(
            top_frame, 
            text="Wyniki wyszukiwania",
            font=('Arial', 10, 'bold')
        )
        self.search_info_label.pack(side='left', padx=5)
        
        # Refresh button
        ttk.Button(
            top_frame, 
            text="Odśwież", 
            command=self.refresh_search
        ).pack(side='right', padx=5)
        
        # PDF engine label (shows current engine selection)
        pdf_engine = self._get_pdf_engine_from_config()
        self.pdf_engine_label = ttk.Label(
            top_frame,
            text=f"Silnik PDF: {pdf_engine}",
            font=('Arial', 8),
            foreground='green'
        )
        self.pdf_engine_label.pack(side='right', padx=10)
        
        # Main content frame with paned window (split view)
        paned = ttk.PanedWindow(self.window, orient=tk.VERTICAL)
        paned.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Top pane: Results table
        table_frame = ttk.Frame(paned)
        paned.add(table_frame, weight=3)
        
        # Create table label
        ttk.Label(
            table_frame, 
            text="Znalezione wiadomości:",
            font=('Arial', 9, 'bold')
        ).pack(anchor='w', padx=5, pady=5)
        
        # Create Treeview for results
        self.tree = ttk.Treeview(
            table_frame,
            columns=('date', 'sender', 'subject', 'folder', 'attachments', 'status'),
            show='headings',
            selectmode='browse'
        )
        
        # Define columns
        self.tree.heading('date', text='Data')
        self.tree.heading('sender', text='Nadawca')
        self.tree.heading('subject', text='Temat')
        self.tree.heading('folder', text='Folder')
        self.tree.heading('attachments', text='Załączniki')
        self.tree.heading('status', text='Status')
        
        # Column widths
        self.tree.column('date', width=120)
        self.tree.column('sender', width=180)
        self.tree.column('subject', width=250)
        self.tree.column('folder', width=150)
        self.tree.column('attachments', width=100)
        self.tree.column('status', width=100)
        
        # Scrollbars for table
        tree_scroll_y = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        tree_scroll_x = ttk.Scrollbar(table_frame, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
        
        # Pack tree and scrollbars
        self.tree.pack(side='left', fill='both', expand=True)
        tree_scroll_y.pack(side='right', fill='y')
        tree_scroll_x.pack(side='bottom', fill='x')
        
        # Bind selection event
        self.tree.bind('<<TreeviewSelect>>', self.on_message_selected)
        self.tree.bind('<Double-1>', self.on_message_double_click)
        
        # Bind right-click for context menu
        self.tree.bind('<Button-3>', self.show_context_menu)  # Right-click on Linux/Windows
        self.tree.bind('<Control-Button-1>', self.show_context_menu)  # Ctrl+Click on macOS (primary method)
        
        # Create context menu (will be populated dynamically)
        self.context_menu = tk.Menu(self.tree, tearoff=0)
        
        # Bottom pane: Details and snippets
        details_frame = ttk.Frame(paned)
        paned.add(details_frame, weight=2)
        
        # Details label
        ttk.Label(
            details_frame,
            text="Dopasowania w PDF:",
            font=('Arial', 9, 'bold')
        ).pack(anchor='w', padx=5, pady=5)
        
        # Snippet display area
        self.snippet_text = scrolledtext.ScrolledText(
            details_frame,
            wrap=tk.WORD,
            height=10,
            font=('Courier', 9)
        )
        self.snippet_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Action buttons frame
        button_frame = ttk.Frame(details_frame)
        button_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(
            button_frame,
            text="Otwórz załącznik",
            command=self.open_attachment
        ).pack(side='left', padx=5)
        
        ttk.Button(
            button_frame,
            text="Pokaż w poczcie",
            command=self.show_in_mail
        ).pack(side='left', padx=5)
        
        # Bottom frame with pagination
        bottom_frame = ttk.Frame(self.window, padding=10)
        bottom_frame.pack(fill='x', side='bottom')
        
        # Results count
        self.results_label = ttk.Label(bottom_frame, text="Znaleziono: 0 wiadomości")
        self.results_label.pack(side='left', padx=5)
        
        # Pagination controls
        pagination_frame = ttk.Frame(bottom_frame)
        pagination_frame.pack(side='right')
        
        ttk.Button(
            pagination_frame,
            text="« Poprzednia",
            command=self.previous_page
        ).pack(side='left', padx=2)
        
        self.page_label = ttk.Label(pagination_frame, text="Strona 1")
        self.page_label.pack(side='left', padx=10)
        
        ttk.Button(
            pagination_frame,
            text="Następna »",
            command=self.next_page
        ).pack(side='left', padx=2)
    
    def start_search(self):
        """Start the search with provided criteria"""
        log("Starting search with criteria")
        
        # Update search info label
        nip = self.search_criteria.get('nip', 'N/A')
        self.search_info_label.config(text=f"Wyszukiwanie NIP: {nip}")
        
        # Clear current results
        self.clear_results()
        
        # Try loading from output_folder first (fast immediate UX)
        output_folder = self.search_criteria.get('output_folder')
        if output_folder:
            self.load_results_from_folder(output_folder)
            return
        
        # Fall back to full search or placeholder
        connection = self.search_criteria.get('connection')
        if search_messages and connection:
            # leave placeholder or implement full search later
            self.show_placeholder_results()
            return
        
        self.show_placeholder_results()
    
    def refresh_search(self):
        """Refresh the current search"""
        if self.search_criteria:
            self.start_search()
        else:
            messagebox.showinfo("Info", "Brak kryteriów wyszukiwania do odświeżenia")
    
    def clear_results(self):
        """Clear the results table"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.snippet_text.delete('1.0', tk.END)
        self.results_label.config(text="Znaleziono: 0 wiadomości")
        self.item_metadata = {}  # Clear metadata dict
    
    def load_results_from_folder(self, folder_path):
        """Load PDF files from folder and display them in results table"""
        self.clear_results()
        if not folder_path:
            return
        # Normalize path for security
        folder_path = os.path.abspath(folder_path)
        if not os.path.isdir(folder_path):
            messagebox.showinfo("Info", f"Folder nie istnieje: {folder_path}")
            return
        try:
            # Get all PDF files
            pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]
            pdf_files.sort()
            
            # Create mapping of EML files (assuming naming pattern: N_email.eml for N_*.pdf)
            eml_files = {}
            for f in os.listdir(folder_path):
                if f.lower().endswith('.eml'):
                    # Extract the number prefix (e.g., "1" from "1_email.eml")
                    parts = f.split('_')
                    if parts:
                        num = parts[0]
                        eml_files[num] = os.path.join(folder_path, f)
            
            for fname in pdf_files:
                full = os.path.join(folder_path, fname)
                try:
                    mtime = datetime.fromtimestamp(os.path.getmtime(full)).strftime('%Y-%m-%d %H:%M')
                except Exception:
                    mtime = '-'
                
                # Try to find corresponding EML file
                eml_path = None
                from_address = '-'
                subject = fname
                
                # Extract number prefix from PDF filename (e.g., "1" from "1_invoice.pdf")
                pdf_parts = fname.split('_')
                if pdf_parts:
                    num = pdf_parts[0]
                    eml_path = eml_files.get(num)
                    
                    # If EML exists, parse it to get sender and subject
                    if eml_path and os.path.isfile(eml_path):
                        try:
                            with open(eml_path, 'rb') as eml_file:
                                eml_message = email.message_from_bytes(eml_file.read())
                                from_header = eml_message.get('From', '-')
                                from_address = self._extract_email_address(from_header)
                                subject_header = eml_message.get('Subject', fname)
                                subject = self._decode_email_subject(subject_header)
                        except Exception as e:
                            log(f"Błąd parsowania EML {eml_path}: {e}", level="WARNING")
                
                # Create metadata object with PDF path and EML path
                metadata = {
                    'pdf_paths': [full],
                    'eml_path': eml_path,
                    'from_address': from_address,
                    'subject': subject
                }
                item_id = self.tree.insert('', 'end', values=(mtime, from_address, subject, folder_path, '1', 'Zapisano'))
                # Store metadata in a dict keyed by item ID
                self.item_metadata[item_id] = metadata
            
            self.results_label.config(text=f"Znaleziono: {len(pdf_files)} plików")
        except Exception as e:
            log(f"Błąd podczas wczytywania folderu wyników: {e}", level="ERROR")
            messagebox.showerror("Błąd", f"Nie udało się wczytać folderu wyników:\n{str(e)}")
    
    def show_placeholder_results(self):
        """Show placeholder results (for demonstration)"""
        # This is a placeholder - in full implementation, would show actual search results
        self.snippet_text.insert('1.0', PLACEHOLDER_TEXT)
        
        self.results_label.config(text="Znaleziono: 0 wiadomości (przykładowe okno)")
    
    def on_message_selected(self, event):
        """Handle message selection in table"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = self.tree.item(selection[0])
        values = item['values']
        
        # Display message info and snippets
        self.snippet_text.delete('1.0', tk.END)
        
        # In full implementation, would fetch PDF matches for this message
        message_info = f"Wybrana wiadomość:\n\n"
        message_info += f"Data: {values[0]}\n"
        message_info += f"Od: {values[1]}\n"
        message_info += f"Temat: {values[2]}\n"
        message_info += f"Folder: {values[3]}\n"
        message_info += f"Załączniki: {values[4]}\n\n"
        message_info += "Dopasowania PDF będą wyświetlane tutaj..."
        
        self.snippet_text.insert('1.0', message_info)
        
        log(f"Message selected: {values[2]}")
    
    def on_message_double_click(self, event):
        """Handle double-click on message - opens PDF attachment"""
        self.open_attachment()
    
    def show_context_menu(self, event):
        """
        Show context menu when user right-clicks on a tree item
        
        Args:
            event: Tkinter event object with x, y coordinates
        """
        # Identify the item under the cursor
        item_id = self.tree.identify_row(event.y)
        
        if not item_id:
            # No item under cursor, don't show menu
            return
        
        # Select the item that was right-clicked
        self.tree.selection_set(item_id)
        self.tree.focus(item_id)
        
        # Clear existing menu items
        self.context_menu.delete(0, tk.END)
        
        # Get metadata for this item
        metadata = self.item_metadata.get(item_id, {})
        pdf_paths = metadata.get('pdf_paths', [])
        eml_path = metadata.get('eml_path')
        
        # Determine which menu items to show based on available files
        has_pdf = bool(pdf_paths and any(os.path.isfile(p) for p in pdf_paths))
        has_eml = bool(eml_path and os.path.isfile(eml_path))
        
        # Add menu items based on availability
        if has_pdf:
            self.context_menu.add_command(
                label="Otwórz PDF",
                command=lambda: self._open_pdf_from_context_menu(item_id)
            )
        
        if has_eml:
            self.context_menu.add_command(
                label="Otwórz Email",
                command=lambda: self._open_email_from_context_menu(item_id)
            )
        
        # Show menu only if at least one option is available
        if has_pdf or has_eml:
            # Display the menu at cursor position
            try:
                self.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                # Make sure to release the grab
                self.context_menu.grab_release()
        else:
            # No files available, show informational message
            messagebox.showinfo(
                "Brak plików",
                "Nie znaleziono plików PDF ani Email dla tej pozycji."
            )
    
    def _open_pdf_from_context_menu(self, item_id):
        """
        Open PDF file from context menu
        
        Args:
            item_id: Treeview item ID
        """
        metadata = self.item_metadata.get(item_id, {})
        pdf_paths = metadata.get('pdf_paths', [])
        
        if not pdf_paths:
            messagebox.showwarning("Ostrzeżenie", "Nie znaleziono ścieżki do pliku PDF")
            return
        
        # Find the first existing PDF file
        pdf_path = None
        for path in pdf_paths:
            if os.path.isfile(path):
                pdf_path = path
                break
        
        if not pdf_path:
            messagebox.showerror(
                "Błąd",
                f"Plik PDF nie istnieje:\n{pdf_paths[0]}"
            )
            log(f"PDF file not found: {pdf_paths[0]}", level="ERROR")
            return
        
        try:
            self._open_file_with_system_app(pdf_path)
            log(f"Opened PDF via context menu: {pdf_path}")
        except Exception as e:
            error_msg = self._format_file_error_message("PDF", pdf_path, e)
            log(f"Error opening PDF via context menu: {e}", level="ERROR")
            messagebox.showerror("Błąd", error_msg)
    
    def _open_email_from_context_menu(self, item_id):
        """
        Open EML file from context menu
        
        Args:
            item_id: Treeview item ID
        """
        metadata = self.item_metadata.get(item_id, {})
        eml_path = metadata.get('eml_path')
        
        if not eml_path:
            messagebox.showwarning("Ostrzeżenie", "Nie znaleziono ścieżki do pliku Email")
            return
        
        if not os.path.isfile(eml_path):
            messagebox.showerror(
                "Błąd",
                f"Plik Email nie istnieje:\n{eml_path}"
            )
            log(f"EML file not found: {eml_path}", level="ERROR")
            return
        
        try:
            self._open_file_with_system_app(eml_path)
            log(f"Opened EML via context menu: {eml_path}")
        except Exception as e:
            error_msg = self._format_file_error_message("Email", eml_path, e)
            log(f"Error opening EML via context menu: {e}", level="ERROR")
            messagebox.showerror("Błąd", error_msg)
    
    def open_attachment(self):
        """Open the selected message's PDF attachment"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Wybierz wiadomość z tabeli")
            return
        
        item_id = selection[0]
        item = self.tree.item(item_id)
        values = item['values']
        
        # Try to get metadata from stored dict
        metadata = self.item_metadata.get(item_id, {})
        pdf_paths = metadata.get('pdf_paths', [])
        
        # If no metadata, try to construct path from folder column
        if not pdf_paths:
            folder_path = values[3]  # Folder column
            filename = values[2]  # Subject/filename column
            if folder_path and folder_path != '-':
                pdf_path = os.path.join(folder_path, filename)
                if os.path.isfile(pdf_path):
                    pdf_paths = [pdf_path]
        
        if not pdf_paths:
            messagebox.showwarning("Ostrzeżenie", "Nie znaleziono ścieżki do załącznika PDF")
            log("No PDF path found for selected item", level="WARNING")
            return
        
        # Find the first existing PDF file
        pdf_path = None
        for path in pdf_paths:
            if os.path.isfile(path):
                pdf_path = path
                break
        
        if not pdf_path:
            messagebox.showerror(
                "Błąd",
                f"Plik PDF nie istnieje:\n{pdf_paths[0]}"
            )
            log(f"PDF file not found: {pdf_paths[0]}", level="ERROR")
            return
        
        try:
            self._open_file_with_system_app(pdf_path)
            log(f"Opened PDF attachment: {pdf_path}")
        except Exception as e:
            error_msg = self._format_file_error_message("PDF", pdf_path, e)
            log(f"Error opening PDF attachment: {e}", level="ERROR")
            messagebox.showerror("Błąd", error_msg)
    
    def show_in_mail(self):
        """Show the selected message in the mail client (open .eml file)"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Wybierz wiadomość z tabeli")
            return
        
        item_id = selection[0]
        
        # Try to get metadata from stored dict
        metadata = self.item_metadata.get(item_id, {})
        eml_path = metadata.get('eml_path')
        
        if not eml_path:
            messagebox.showwarning("Ostrzeżenie", 
                "Plik .eml nie jest dostępny.\n\n"
                "Ta funkcja działa tylko gdy wiadomości są zapisane jako pliki .eml na dysku.")
            log("No EML path found for selected item", level="WARNING")
            return
        
        if not os.path.isfile(eml_path):
            messagebox.showerror(
                "Błąd",
                f"Plik Email nie istnieje:\n{eml_path}"
            )
            log(f"EML file not found: {eml_path}", level="ERROR")
            return
        
        try:
            self._open_file_with_system_app(eml_path)
            log(f"Opened EML file: {eml_path}")
        except Exception as e:
            error_msg = self._format_file_error_message("Email", eml_path, e)
            log(f"Error opening EML file: {e}", level="ERROR")
            messagebox.showerror("Błąd", error_msg)
    
    def _format_file_error_message(self, file_type, file_path, error):
        """
        Format a consistent error message for file opening failures
        
        Args:
            file_type: Type of file (e.g., "PDF", "Email")
            file_path: Path to the file that failed to open
            error: Exception or error message string
            
        Returns:
            str: Formatted error message
        """
        return f"Nie udało się otworzyć pliku {file_type}:\n\nŚcieżka: {file_path}\n\nBłąd: {str(error)}"
    
    def _open_file_with_system_app(self, file_path):
        """
        Open a file with the system's default application
        
        Args:
            file_path: Path to the file to open
            
        Raises:
            Exception: If file cannot be opened
        """
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"Plik nie istnieje: {file_path}")
        
        try:
            if sys.platform == 'win32':
                # Windows
                os.startfile(file_path)
            elif sys.platform == 'darwin':
                # macOS
                subprocess.run(['open', file_path], check=True)
            else:
                # Linux and other Unix-like
                subprocess.run(['xdg-open', file_path], check=True)
        except subprocess.CalledProcessError as e:
            raise Exception(f"Nie można uruchomić aplikacji: {str(e)}")
        except Exception as e:
            raise Exception(f"Błąd podczas otwierania pliku: {str(e)}")
    
    def _extract_email_address(self, from_header):
        """
        Extract email address from From header
        
        Args:
            from_header: Email From header (e.g., "John Doe <john@example.com>")
            
        Returns:
            str: Email address or original string if parsing fails
        """
        if not from_header:
            return '-'
        
        # Try to extract email from format "Name <email@example.com>"
        email_pattern = r'<([^>]+)>'
        match = re.search(email_pattern, from_header)
        if match:
            return match.group(1)
        
        # If no angle brackets, return as-is (might already be just email)
        return from_header.strip()
    
    def _decode_email_subject(self, subject):
        """
        Decode email subject handling encoded headers
        
        Args:
            subject: Email subject string (possibly encoded)
            
        Returns:
            str: Decoded subject
        """
        if not subject:
            return ""
        
        decoded_parts = []
        try:
            for part, encoding in decode_header(subject):
                if isinstance(part, bytes):
                    try:
                        decoded_parts.append(part.decode(encoding or 'utf-8'))
                    except (UnicodeDecodeError, LookupError):
                        decoded_parts.append(part.decode('utf-8', errors='ignore'))
                else:
                    decoded_parts.append(str(part))
            return ''.join(decoded_parts)
        except Exception:
            return subject
    
    def previous_page(self):
        """Go to previous page of results"""
        if self.current_page > 0:
            self.current_page -= 1
            self.load_page()
    
    def next_page(self):
        """Go to next page of results"""
        # Calculate max pages
        total = self.results.get('total_count', 0)
        max_pages = (total + self.per_page - 1) // self.per_page
        
        if self.current_page < max_pages - 1:
            self.current_page += 1
            self.load_page()
    
    def load_page(self):
        """Load the current page of results"""
        self.page_label.config(text=f"Strona {self.current_page + 1}")
        # In full implementation, would load results for current page
        log(f"Loading page {self.current_page + 1}")


def open_znalezione_window(parent, search_criteria=None):
    """
    Convenience function to open the Znalezione window
    
    Args:
        parent: Parent Tkinter widget
        search_criteria: Optional dict with search parameters
        
    Returns:
        ZnalezioneWindow instance
    """
    return ZnalezioneWindow(parent, search_criteria)
