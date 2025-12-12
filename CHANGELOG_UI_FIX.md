# Changelog - Fix for "Znalezione" Tab and Live Results

## Changes Made

### 1. UI Structure Reorganization
- **Moved "Znalezione" tab**: The "Znalezione" (Found) tab is no longer a top-level tab
- **Created nested notebook**: Inside the "Wyszukiwanie NIP" tab, there are now two sub-tabs:
  - **"Wyniki"**: Shows search logs and progress
  - **"Znalezione"**: Shows live list of found files as they are discovered
- **Removed old top-level tab**: The old "Znalezione" tab that appeared as the 3rd main tab has been removed

### 2. Live Result Streaming
- **Real-time updates**: Found files now appear immediately in the "Znalezione" sub-tab as soon as they are discovered
- **Queue-based communication**: Uses the existing `log_queue` with enhanced message types
- **Thread-safe polling**: The GUI polls the queue every 200ms using `root.after()` for smooth updates
- **Two message types**:
  - `{'type': 'log', 'message': '...'}` - for progress logs
  - `{'type': 'found', 'path': '...'}` - for found files

### 3. Code Changes

#### poczta_faktury.py
- Modified `create_widgets()`: Removed top-level "Znalezione" tab
- Rewrote `create_search_tab()`: Added inner notebook with "Wyniki" and "Znalezione" tabs
- Updated `_poll_log_queue()`: Now handles both 'log' and 'found' message types
- Updated `safe_log()`: Now wraps messages in dict format `{'type': 'log', 'message': ...}`
- Modified `start_search_thread()`: Clears the live found listbox on new search
- Enhanced `_search_with_imap_threaded()`: Pushes found files to queue immediately after saving

#### search_worker.py (new file)
- Created `SearchStop` event class for future extensibility
- Provides a clean module structure for search worker functionality

### 4. Documentation Updates
- Updated USAGE.md to reflect new UI structure
- Added explanation of the nested tab structure
- Updated instructions for viewing results

## Testing

All structural tests pass:
- ✓ UI structure correctly reorganized with nested notebooks
- ✓ Polling mechanism handles both log and found message types
- ✓ Search worker module created with required classes
- ✓ Live result push implemented in IMAP search
- ✓ Top-level tabs reduced from 4 to 3

## Benefits

1. **Better UX**: Found files appear immediately, not just at the end of search
2. **Cleaner organization**: Search-related information grouped together in one place
3. **Responsive feedback**: Users can see progress in real-time
4. **Backward compatible**: Old saved invoice data still accessible
5. **Thread-safe**: All GUI updates happen in the main thread via polling

## Migration Notes

- No user action required - the new structure will appear automatically
- Old configuration files remain compatible
- Previously saved invoices remain accessible
