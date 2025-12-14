"""
Znalezione (Found) - Search Results Window

This window displays search results from email searches, including:
- Results table with columns (date, sender, subject, folder, attachments, status)
- PDF snippet display showing matched text from attachments
- Action buttons (Open Attachment, Download, Show in Mail)
- Pagination support

Source: Created for Poczta-Faktury based on design from dzieju-app2
Layout inspiration: https://github.com/dzieju/dzieju-app2/blob/fcee6b91bf240d17ceb38f8564beab5aa9637437/imap_tab_visual_mockup.html
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
import os

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
            text="Pobierz",
            command=self.download_attachment
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
            files = [f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]
            files.sort()
            for fname in files:
                full = os.path.join(folder_path, fname)
                try:
                    mtime = datetime.fromtimestamp(os.path.getmtime(full)).strftime('%Y-%m-%d %H:%M')
                except Exception:
                    mtime = '-'
                self.tree.insert('', 'end', values=(mtime, '-', fname, folder_path, '1', 'Zapisano'))
            self.results_label.config(text=f"Znaleziono: {len(files)} plików")
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
        """Handle double-click on message"""
        self.show_in_mail()
    
    def open_attachment(self):
        """Open the selected message's attachment"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Wybierz wiadomość z tabeli")
            return
        
        messagebox.showinfo("Info", "Funkcja otwierania załącznika zostanie zaimplementowana")
        log("Open attachment requested")
    
    def download_attachment(self):
        """Download the selected message's attachment"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Wybierz wiadomość z tabeli")
            return
        
        messagebox.showinfo("Info", "Funkcja pobierania załącznika zostanie zaimplementowana")
        log("Download attachment requested")
    
    def show_in_mail(self):
        """Show the selected message in the mail client"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Wybierz wiadomość z tabeli")
            return
        
        messagebox.showinfo("Info", "Funkcja pokazania w kliencie pocztowym zostanie zaimplementowana")
        log("Show in mail requested")
    
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
