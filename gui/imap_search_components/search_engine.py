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
import email
import email.utils
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


# IMAP date formatting helper functions

def _imap_date_str(dt):
    """
    Format a datetime object to IMAP date string format (dd-Mon-YYYY).
    
    IMAP SEARCH command expects dates in the format: dd-Mon-YYYY
    Example: 15-Dec-2024
    
    Args:
        dt: datetime object to format
        
    Returns:
        str: Formatted date string for IMAP SEARCH (e.g., "15-Dec-2024")
    """
    if not dt:
        return None
    # Format: dd-Mon-YYYY (e.g., "15-Dec-2024")
    return dt.strftime("%d-%b-%Y")


def _normalize_date_range(criteria):
    """
    Convert GUI date criteria (named ranges or explicit dates) to datetime objects.
    
    Supports both explicit datetime objects and named ranges:
    - 'range_week': Last 7 days inclusive (today and previous 6 days)
    - 'range_1m': Last 30 days
    - 'range_3m': Last 90 days
    - 'range_6m': Last 180 days
    
    Args:
        criteria: dict with optional 'date_from', 'date_to', 'range_week', 
                 'range_1m', 'range_3m', 'range_6m' keys
                 
    Returns:
        tuple: (date_from, date_to) as datetime objects, or (None, None) if no date filtering
    """
    date_from = criteria.get('date_from')
    date_to = criteria.get('date_to')
    
    # If explicit dates provided, use them
    if date_from and date_to:
        # Normalize to start/end of day
        if hasattr(date_from, 'replace'):
            date_from = date_from.replace(hour=0, minute=0, second=0, microsecond=0)
        if hasattr(date_to, 'replace'):
            date_to = date_to.replace(hour=23, minute=59, second=59, microsecond=999999)
        return (date_from, date_to)
    
    # Check for named range flags
    today = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
    
    # Define 'week' as last 7 days inclusive (today and previous 6 days)
    if criteria.get('range_week'):
        date_from = (today - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
        date_to = today
        log(f"Using 'week' range: {date_from.strftime('%Y-%m-%d')} to {date_to.strftime('%Y-%m-%d')} (last 7 days inclusive)")
        return (date_from, date_to)
    
    if criteria.get('range_1m'):
        date_from = (today - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
        date_to = today
        return (date_from, date_to)
    
    if criteria.get('range_3m'):
        date_from = (today - timedelta(days=90)).replace(hour=0, minute=0, second=0, microsecond=0)
        date_to = today
        return (date_from, date_to)
    
    if criteria.get('range_6m'):
        date_from = (today - timedelta(days=180)).replace(hour=0, minute=0, second=0, microsecond=0)
        date_to = today
        return (date_from, date_to)
    
    # No date filtering
    return (None, None)


def imap_search_uids_for_date_range(imap_conn, folder, date_from, date_to, extra_criteria=None):
    """
    Perform server-side IMAP UID SEARCH with SINCE/BEFORE date criteria.
    
    IMAP date semantics:
    - SINCE <date>: Messages with internal date >= <date> (inclusive)
    - BEFORE <date>: Messages with internal date < <date> (exclusive)
    
    To include messages on date_to, we must use BEFORE (date_to + 1 day).
    Example: To get messages from Dec 1 to Dec 7 inclusive:
      SINCE 01-Dec-2024 BEFORE 08-Dec-2024
    
    Args:
        imap_conn: IMAP connection object (imaplib.IMAP4_SSL or similar)
        folder: Folder name to search (e.g., 'INBOX')
        date_from: Start date (datetime object, inclusive)
        date_to: End date (datetime object, inclusive)
        extra_criteria: Optional list of additional IMAP search criteria
        
    Returns:
        list: List of UIDs (as strings) matching the criteria, or None on error
    """
    try:
        # Select folder
        status, data = imap_conn.select(folder, readonly=True)
        if status != 'OK':
            log(f"Failed to select folder {folder}: {data}", level="ERROR")
            return None
        
        # Build search criteria
        search_parts = []
        
        if date_from:
            since_str = _imap_date_str(date_from)
            search_parts.append(f'SINCE {since_str}')
            log(f"IMAP SEARCH: SINCE {since_str}")
        
        if date_to:
            # IMPORTANT: BEFORE is exclusive, so we add 1 day to include date_to
            # Example: To include Dec 7, we use BEFORE 08-Dec
            before_date = date_to + timedelta(days=1)
            before_str = _imap_date_str(before_date)
            search_parts.append(f'BEFORE {before_str}')
            log(f"IMAP SEARCH: BEFORE {before_str} (to include {_imap_date_str(date_to)})")
        
        if extra_criteria:
            search_parts.extend(extra_criteria)
        
        # Combine all criteria
        search_query = ' '.join(search_parts) if search_parts else 'ALL'
        
        log(f"Executing IMAP UID SEARCH in {folder}: {search_query}")
        
        # Execute UID SEARCH
        status, data = imap_conn.uid('search', None, search_query)
        
        if status != 'OK':
            log(f"IMAP UID SEARCH failed: {data}", level="WARNING")
            return None
        
        # Parse UIDs from response
        if not data or not data[0]:
            log(f"No messages found in {folder} matching criteria")
            return []
        
        uids = data[0].decode('utf-8').split()
        log(f"Found {len(uids)} UIDs in {folder} matching date range")
        
        return uids
        
    except Exception as e:
        log(f"Error in imap_search_uids_for_date_range: {str(e)}", level="ERROR")
        return None


def filter_uids_by_internaldate(imap_conn, folder, uids, date_from, date_to):
    """
    Client-side fallback: Fetch INTERNALDATE for UIDs and filter by date range.
    
    This is used when server-side IMAP SEARCH fails or is not supported.
    Fetches INTERNALDATE for each UID and filters locally.
    
    Args:
        imap_conn: IMAP connection object
        folder: Folder name
        uids: List of UIDs to filter
        date_from: Start date (datetime object, inclusive)
        date_to: End date (datetime object, inclusive)
        
    Returns:
        list: Filtered list of UIDs matching the date range
    """
    if not uids:
        return []
    
    try:
        # Select folder
        status, data = imap_conn.select(folder, readonly=True)
        if status != 'OK':
            log(f"Failed to select folder {folder} for filtering", level="ERROR")
            return uids  # Return all UIDs if we can't filter
        
        filtered_uids = []
        
        # Fetch INTERNALDATE in batches to avoid overwhelming the server
        batch_size = 200
        for i in range(0, len(uids), batch_size):
            batch_uids = uids[i:i+batch_size]
            uid_range = ','.join(batch_uids)
            
            # Fetch INTERNALDATE for this batch
            status, data = imap_conn.uid('fetch', uid_range, '(INTERNALDATE)')
            
            if status != 'OK':
                log(f"Failed to fetch INTERNALDATE for batch {i//batch_size + 1}", level="WARNING")
                filtered_uids.extend(batch_uids)  # Include all from failed batch
                continue
            
            # Parse INTERNALDATE from each response
            for response in data:
                if not response or not isinstance(response, tuple):
                    continue
                
                response_str = response[0].decode('utf-8', errors='ignore')
                
                # Extract UID and INTERNALDATE
                # Format: UID 123 (INTERNALDATE "15-Dec-2024 10:30:00 +0000")
                uid_match = re.search(r'UID (\d+)', response_str)
                date_match = re.search(r'INTERNALDATE "([^"]+)"', response_str)
                
                if not uid_match or not date_match:
                    continue
                
                uid = uid_match.group(1)
                date_str = date_match.group(1)
                
                # Parse INTERNALDATE
                try:
                    # INTERNALDATE format: "15-Dec-2024 10:30:00 +0000"
                    msg_date = email.utils.parsedate_to_datetime(date_str)
                    
                    # Check if date is in range
                    in_range = True
                    if date_from and msg_date < date_from:
                        in_range = False
                    if date_to and msg_date > date_to:
                        in_range = False
                    
                    if in_range:
                        filtered_uids.append(uid)
                        
                except Exception as e:
                    log(f"Error parsing INTERNALDATE for UID {uid}: {e}", level="WARNING")
                    filtered_uids.append(uid)  # Include on parse error
        
        log(f"Client-side filtering: {len(filtered_uids)}/{len(uids)} UIDs match date range")
        return filtered_uids
        
    except Exception as e:
        log(f"Error in filter_uids_by_internaldate: {str(e)}", level="ERROR")
        return uids  # Return all UIDs on error


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
            - 'range_week': Search last 7 days (optional boolean flag)
            - 'range_1m': Search last 30 days (optional boolean flag)
            - 'range_3m': Search last 90 days (optional boolean flag)
            - 'range_6m': Search last 180 days (optional boolean flag)
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
    
    log(f"search_messages called with criteria: {list(criteria.keys())}")
    
    # Extract criteria
    nip = criteria.get('nip', '').strip()
    connection = criteria.get('connection')
    per_page = criteria.get('per_page', 500)
    page = criteria.get('page', 0)
    folder_path = criteria.get('folder_path')
    excluded_folders = criteria.get('excluded_folders', '').split(',') if criteria.get('excluded_folders') else []
    cancel_check = criteria.get('_cancel_check', lambda: False)
    
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
    
    # Normalize date range from criteria
    date_from, date_to = _normalize_date_range(criteria)
    
    if date_from and date_to:
        log(f"Searching for NIP: {nip} with date range: {date_from.strftime('%Y-%m-%d')} to {date_to.strftime('%Y-%m-%d')}")
    else:
        log(f"Searching for NIP: {nip} (no date filter)")
    
    # Initialize results structure
    results = {
        'messages': [],
        'message_to_folder_map': {},
        'matches': {},
        'folder_results': {},
        'total_count': 0,
        'error': None
    }
    
    # Initialize PDF processor if available
    pdf_processor = None
    if PDFProcessor:
        pdf_processor = PDFProcessor()
    
    try:
        # Determine folders to search
        folders_to_search = []
        if folder_path:
            folders_to_search = [folder_path]
        else:
            # Try to list all folders
            try:
                status, folder_list = connection.list()
                if status == 'OK':
                    for folder_info in folder_list:
                        if not folder_info:
                            continue
                        # Parse folder name from IMAP LIST response
                        # Format: (\\HasNoChildren) "/" "INBOX"
                        folder_match = re.search(r'"([^"]+)"$', folder_info.decode('utf-8', errors='ignore'))
                        if folder_match:
                            folder_name = folder_match.group(1)
                            if folder_name not in excluded_folders:
                                folders_to_search.append(folder_name)
                else:
                    # Fallback to INBOX only
                    folders_to_search = ['INBOX']
            except Exception as e:
                log(f"Error listing folders: {e}, using INBOX only", level="WARNING")
                folders_to_search = ['INBOX']
        
        log(f"Searching in {len(folders_to_search)} folder(s): {folders_to_search}")
        
        total_processed = 0
        
        # Search each folder
        for folder_idx, folder in enumerate(folders_to_search):
            # Check for cancellation
            if cancel_check():
                log("Search cancelled by user")
                results['error'] = 'Wyszukiwanie przerwane przez użytkownika'
                break
            
            if progress_callback:
                folder_progress = int((folder_idx / len(folders_to_search)) * 90)
                progress_callback(f"Przeszukiwanie folderu: {folder}", folder_progress)
            
            log(f"Searching folder: {folder}")
            
            # Try server-side IMAP date search first
            uids = None
            if date_from or date_to:
                uids = imap_search_uids_for_date_range(connection, folder, date_from, date_to)
            
            # If server-side search failed or no date filter, get all UIDs
            if uids is None:
                try:
                    status, data = connection.select(folder, readonly=True)
                    if status == 'OK':
                        status, data = connection.uid('search', None, 'ALL')
                        if status == 'OK' and data and data[0]:
                            all_uids = data[0].decode('utf-8').split()
                            
                            # Apply client-side date filtering if needed
                            if date_from or date_to:
                                log(f"Server-side date search failed, applying client-side filter to {len(all_uids)} UIDs")
                                uids = filter_uids_by_internaldate(connection, folder, all_uids, date_from, date_to)
                            else:
                                uids = all_uids
                        else:
                            log(f"No messages in folder {folder}")
                            continue
                    else:
                        log(f"Failed to select folder {folder}", level="WARNING")
                        continue
                except Exception as e:
                    log(f"Error searching folder {folder}: {e}", level="ERROR")
                    continue
            
            if not uids:
                log(f"No messages found in {folder} matching criteria")
                continue
            
            log(f"Processing {len(uids)} messages in {folder}")
            
            # Process UIDs in batches to avoid memory/IO storms
            batch_size = 200
            messages_found = 0
            
            for batch_idx in range(0, len(uids), batch_size):
                # Check for cancellation
                if cancel_check():
                    log("Search cancelled by user during batch processing")
                    break
                
                batch_uids = uids[batch_idx:batch_idx + batch_size]
                uid_range = ','.join(batch_uids)
                
                try:
                    # Fetch message headers and structure
                    status, data = connection.uid('fetch', uid_range, '(BODY.PEEK[HEADER] BODYSTRUCTURE)')
                    
                    if status != 'OK':
                        log(f"Failed to fetch batch {batch_idx//batch_size + 1} in {folder}", level="WARNING")
                        continue
                    
                    # Process each message in the batch
                    # IMAP can return mixed results, so we process each item individually
                    for item in data:
                        if not item or not isinstance(item, tuple) or len(item) < 2:
                            continue
                        
                        total_processed += 1
                        
                        # Update progress periodically
                        if total_processed % 50 == 0 and progress_callback:
                            progress = min(90, folder_progress + int((total_processed / len(uids)) * 10))
                            progress_callback(f"Przetworzono {total_processed} wiadomości w {folder}", progress)
                        
                        # Parse message
                        try:
                            # item is a tuple: (header_line, header_data)
                            raw_headers = item[1]
                            msg = email.message_from_bytes(raw_headers)
                            
                            # Extract UID from header_line
                            uid_match = re.search(r'UID (\d+)', item[0].decode('utf-8', errors='ignore'))
                            msg_uid = uid_match.group(1) if uid_match else str(total_processed)
                            
                            # Check if message has PDF attachments (simplified check from BODYSTRUCTURE)
                            # For now, we'll fetch full message if needed
                            # TODO: More efficient attachment detection from BODYSTRUCTURE
                            
                            # Fetch full message to check attachments
                            status, msg_data = connection.uid('fetch', msg_uid, '(BODY.PEEK[])')
                            if status != 'OK' or not msg_data or not msg_data[0]:
                                continue
                            
                            if isinstance(msg_data[0], tuple):
                                full_msg = email.message_from_bytes(msg_data[0][1])
                            else:
                                continue
                            
                            # Look for PDF attachments
                            has_pdf = False
                            pdf_matches = []
                            
                            for part in full_msg.walk():
                                if part.get_content_maintype() == 'multipart':
                                    continue
                                
                                filename = part.get_filename()
                                if filename and filename.lower().endswith('.pdf'):
                                    has_pdf = True
                                    
                                    # Extract and search PDF if processor available
                                    if pdf_processor:
                                        # Check for cancellation before processing PDF
                                        if cancel_check():
                                            break
                                        
                                        try:
                                            pdf_content = part.get_payload(decode=True)
                                            if pdf_content:
                                                result = pdf_processor.search_in_pdf_attachment(
                                                    pdf_content, nip, filename
                                                )
                                                if result.get('found'):
                                                    pdf_matches.extend(result.get('matches', []))
                                        except Exception as e:
                                            log(f"Error processing PDF {filename}: {e}", level="WARNING")
                            
                            # If PDF found with NIP match, add to results
                            if pdf_matches:
                                message_id = msg.get('Message-ID', msg_uid)
                                
                                message_obj = {
                                    'id': message_id,
                                    'uid': msg_uid,
                                    'subject': msg.get('Subject', ''),
                                    'from': msg.get('From', ''),
                                    'date': msg.get('Date', ''),
                                    'folder': folder,
                                    'has_pdf': has_pdf
                                }
                                
                                results['messages'].append(message_obj)
                                results['message_to_folder_map'][message_id] = folder
                                results['matches'][message_id] = pdf_matches
                                messages_found += 1
                                
                                log(f"Found match in message UID {msg_uid}: {msg.get('Subject', 'No Subject')}")
                        
                        except Exception as e:
                            log(f"Error processing message: {e}", level="WARNING")
                            continue
                
                except Exception as e:
                    log(f"Error fetching batch in {folder}: {e}", level="ERROR")
                    continue
            
            # Store folder results
            results['folder_results'][folder] = {
                'total_checked': len(uids),
                'matches_found': messages_found
            }
            
            log(f"Folder {folder}: found {messages_found} matches in {len(uids)} messages")
        
        # Update total count
        results['total_count'] = len(results['messages'])
        
        if progress_callback:
            progress_callback(f"Wyszukiwanie zakończone. Znaleziono {results['total_count']} wiadomości", 100)
        
        log(f"Search completed. Found {results['total_count']} messages with NIP matches")
    
    except Exception as e:
        log(f"Error in search_messages: {str(e)}", level="ERROR")
        results['error'] = str(e)
    
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
            # Add cancellation checker to criteria
            search_criteria['_cancel_check'] = lambda: self.search_cancelled
            
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
