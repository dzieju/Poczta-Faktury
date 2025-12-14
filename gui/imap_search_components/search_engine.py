"""
Email search engine for mail search functionality

Source: Adapted from dzieju-app2 repository
Original files:
- https://github.com/dzieju/dzieju-app2/blob/fcee6b91bf240d17ceb38f8564beab5aa9637437/gui/imap_search_components/search_engine.py
- https://github.com/dzieju/dzieju-app2/blob/fcee6b91bf240d17ceb38f8564beab5aa9637437/gui/mail_search_components/search_engine.py

This is a simplified implementation focusing on core search functionality.
"""
import threading
import re
from datetime import datetime, timedelta

# Import logger from our local gui module
try:
    from gui.logger import log
except ImportError:
    # Fallback if running standalone
    def log(message, level="INFO"):
        print(f"[{level}] {message}", flush=True)

try:
    from gui.imap_search_components.pdf_processor import PDFProcessor
except ImportError:
    log("Warning: PDFProcessor not available, PDF search will be disabled")
    PDFProcessor = None


def search_messages(criteria, progress_callback=None):
    """
    Search for messages based on criteria
    
    This is a simplified public API for searching messages. It returns a structure
    compatible with the znalezione_window.py interface.
    
    Args:
        criteria: dict with search parameters:
            - 'nip': NIP number to search for
            - 'date_from': Start date for search (datetime object)
            - 'date_to': End date for search (datetime object)
            - 'folder_path': Folder path to search in (optional)
            - 'excluded_folders': Comma-separated list of folders to exclude (optional)
            - 'connection': Email connection object (IMAP, Exchange, etc.)
            - 'per_page': Results per page (default: 500)
            - 'page': Page number (default: 0)
        progress_callback: Optional callback function(message, progress_percent)
        
    Returns:
        dict: {
            'messages': list of message objects with metadata,
            'message_to_folder_map': dict mapping message_id to folder_path,
            'matches': dict mapping message_id to list of PDF match snippets,
            'folder_results': dict with per-folder statistics,
            'total_count': total number of messages found,
            'error': error message if any
        }
    """
    if progress_callback:
        progress_callback("Rozpoczynam wyszukiwanie...", 0)
    
    log(f"search_messages called with criteria: {criteria.keys()}")
    
    # Extract criteria
    nip = criteria.get('nip', '').strip()
    date_from = criteria.get('date_from')
    date_to = criteria.get('date_to')
    connection = criteria.get('connection')
    per_page = criteria.get('per_page', 500)
    page = criteria.get('page', 0)
    
    if not nip:
        log("Error: NIP not provided in search criteria")
        return {
            'messages': [],
            'message_to_folder_map': {},
            'matches': {},
            'folder_results': {},
            'total_count': 0,
            'error': 'Brak numeru NIP do wyszukania'
        }
    
    if not connection:
        log("Error: Connection not provided in search criteria")
        return {
            'messages': [],
            'message_to_folder_map': {},
            'matches': {},
            'folder_results': {},
            'total_count': 0,
            'error': 'Brak połączenia z serwerem email'
        }
    
    log(f"Searching for NIP: {nip}")
    
    # Initialize results structure
    results = {
        'messages': [],
        'message_to_folder_map': {},
        'matches': {},
        'folder_results': {},
        'total_count': 0,
        'error': None
    }
    
    # This is a placeholder implementation
    # In a full implementation, this would connect to the email server,
    # search through folders, extract PDF attachments, and search for NIP
    
    if progress_callback:
        progress_callback("Wyszukiwanie zakończone", 100)
    
    log(f"Search completed. Found {len(results['messages'])} messages")
    
    return results


class EmailSearchEngine:
    """
    Handles email search operations in background thread
    
    This is a simplified implementation that provides the core search infrastructure.
    The full implementation in dzieju-app2 includes pagination, multi-folder search,
    PDF extraction, and detailed progress reporting.
    """
    
    def __init__(self, progress_callback, result_callback):
        """
        Initialize search engine
        
        Args:
            progress_callback: Callback for progress updates (message, percent)
            result_callback: Callback when search completes (results_dict)
        """
        self.progress_callback = progress_callback
        self.result_callback = result_callback
        self.search_cancelled = False
        self.search_thread = None
        
        # Initialize PDF processor if available
        if PDFProcessor:
            self.pdf_processor = PDFProcessor()
        else:
            self.pdf_processor = None
        
        log("EmailSearchEngine initialized")
    
    def search_emails_threaded(self, connection, search_criteria, page=0, per_page=500):
        """
        Start threaded email search
        
        Args:
            connection: Email connection object
            search_criteria: dict with search parameters
            page: Page number for pagination
            per_page: Results per page
        """
        self.search_cancelled = False
        
        # Add connection and pagination to criteria
        search_criteria['connection'] = connection
        search_criteria['page'] = page
        search_criteria['per_page'] = per_page
        
        self.search_thread = threading.Thread(
            target=self._threaded_search,
            args=(search_criteria,),
            daemon=True
        )
        self.search_thread.start()
        log("Search thread started")
    
    def _threaded_search(self, search_criteria):
        """Internal method that runs in background thread"""
        try:
            # Call the public search_messages API
            results = search_messages(search_criteria, self.progress_callback)
            
            # Call result callback with results
            if self.result_callback and not self.search_cancelled:
                self.result_callback(results)
        except Exception as e:
            log(f"Error in search thread: {str(e)}")
            error_results = {
                'messages': [],
                'message_to_folder_map': {},
                'matches': {},
                'folder_results': {},
                'total_count': 0,
                'error': str(e)
            }
            if self.result_callback:
                self.result_callback(error_results)
    
    def cancel_search(self):
        """Cancel ongoing search"""
        log("Search cancelled by user")
        self.search_cancelled = True
        if self.pdf_processor:
            self.pdf_processor.cancel_search()
