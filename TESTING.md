# Testing Guide for Search Results Window Enhancements

This guide describes how to manually test the new features added to the "Znalezione - Wyniki wyszukiwania" (Search Results) window.

## Changes Implemented

### 1. Display Sender Email Address in "Nadawca" Column ✓
- The search results table now displays the sender's email address in the "Nadawca" (Sender) column
- Email addresses are extracted from the "From" header of saved .eml files
- Supports various email formats: `name@domain.com` or `"Name" <name@domain.com>`

### 2. Double-Click Opens PDF Attachments ✓
- Double-clicking on any row in the results table opens the corresponding PDF file
- PDF files are opened using the system's default PDF viewer application
- Works cross-platform (Windows, macOS, Linux)

### 3. "Otwórz załącznik" Button Opens PDF Files ✓
- The "Otwórz załącznik" (Open Attachment) button opens the selected PDF file
- Uses the system's default application for PDF files
- Shows appropriate error messages if file is not found or cannot be opened

### 4. "Pokaż w poczcie" Button Opens EML Files ✓
- The "Pokaż w poczcie" (Show in Mail) button opens the complete email message
- Opens .eml files in the system's default email client
- Automatically saves .eml files alongside PDF files during search
- Shows informative message if .eml file is not available

### 5. Removed "Pobierz" Button ✓
- The "Pobierz" (Download) button has been removed from the UI
- This simplifies the interface and removes redundant functionality

## Manual Testing Instructions

### Prerequisites
1. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   python3 poczta_faktury.py
   ```

### Test Scenario 1: Search and View Results

1. **Configure Email Connection**
   - Go to "Konfiguracja poczty" tab
   - Enter your email server details (IMAP or POP3)
   - Click "Testuj połączenie" to verify connection

2. **Perform Search**
   - Go to "Wyszukiwanie NIP" tab
   - Enter a NIP number (e.g., 1234567890)
   - Select an output folder for saving results
   - Click "Szukaj faktur" to start the search

3. **Open Search Results Window**
   - After search completes, click "Znalezione ➜" button
   - The search results window should open displaying found invoices

4. **Verify Sender Column**
   - Check that the "Nadawca" (Sender) column displays email addresses
   - Email addresses should be extracted from the "From" header
   - Format should be clean (e.g., `sender@example.com` not `"Name" <sender@example.com>`)

### Test Scenario 2: Open PDF Attachments

1. **Double-Click on Row**
   - In the search results window, double-click on any row
   - The corresponding PDF file should open in your default PDF viewer
   - Verify the PDF displays correctly

2. **Use "Otwórz załącznik" Button**
   - Select a row in the table
   - Click the "Otwórz załącznik" button
   - The PDF should open in your default PDF viewer

3. **Error Handling**
   - Try selecting a row where the PDF file doesn't exist (manually delete the PDF)
   - Should display error message: "Nie znaleziono ścieżki do załącznika PDF"

### Test Scenario 3: Open Email Messages

1. **Use "Pokaż w poczcie" Button**
   - Select a row in the results table
   - Click "Pokaż w poczcie" button
   - The .eml file should open in your default email client (e.g., Outlook, Thunderbird, Mail.app)
   - Verify you can see the complete email with headers, body, and attachments

2. **Error Handling**
   - If .eml file is not available, should display warning:
     "Plik .eml nie jest dostępny. Ta funkcja działa tylko gdy wiadomości są zapisane jako pliki .eml na dysku."

### Test Scenario 4: Verify UI Changes

1. **Check Button Layout**
   - Verify only two buttons are visible in the action area:
     - "Otwórz załącznik"
     - "Pokaż w poczcie"
   - The "Pobierz" button should no longer be present

2. **Check Table Columns**
   - Verify the table has these columns in order:
     - Data (Date)
     - Nadawca (Sender) - should show email addresses
     - Temat (Subject)
     - Folder
     - Załączniki (Attachments)
     - Status

## Automated Tests

Run the included test scripts to verify functionality:

```bash
# Unit tests
python3 test_znalezione_window.py

# Integration tests
python3 test_integration.py

# Basic app tests
python3 test_basic.py
```

All tests should pass with output showing ✓ for each test case.

## Expected File Structure

After a successful search, the output folder should contain:

```
output_folder/
├── 1_invoice_name.pdf        # First found PDF
├── 1_email.eml               # Complete email message for first PDF
├── 2_another_invoice.pdf     # Second found PDF
├── 2_email.eml               # Complete email message for second PDF
├── ...
```

The naming pattern `N_*` where N is a sequential number allows the application to match PDFs with their corresponding email messages.

## Platform-Specific Notes

### Windows
- PDF files open with default PDF reader (Adobe Reader, Edge, etc.)
- EML files open with default email client (Outlook, Windows Mail, etc.)
- Uses `os.startfile()` for opening files

### macOS
- PDF files open with Preview or configured PDF reader
- EML files open with Mail.app or configured email client
- Uses `open` command for opening files

### Linux
- PDF files open with default PDF viewer (Evince, Okular, etc.)
- EML files open with default email client (Thunderbird, Evolution, etc.)
- Uses `xdg-open` command for opening files

## Troubleshooting

### PDF won't open
- Verify the file exists in the output folder
- Check that you have a PDF viewer installed and set as default
- Check file permissions

### EML won't open
- Verify the .eml file exists (only created during new searches after this update)
- Check that you have an email client installed and set as default for .eml files
- On Linux, you may need to install and configure a mail client

### Email address not showing
- Verify the .eml file exists and contains a "From" header
- For old search results (before this update), .eml files won't exist

### Error messages
- "Nie znaleziono ścieżki do załącznika PDF" - PDF file is missing
- "Plik .eml nie jest dostępny" - EML file is missing (expected for old results)
- "Nie udało się otworzyć załącznika" - System cannot open the file (no default app configured)

## Development Notes

### Code Changes Summary

1. **znalezione_window.py**
   - Added `item_metadata` dict to store rich metadata for each tree item
   - Implemented `_open_file_with_system_app()` method for cross-platform file opening
   - Implemented `_extract_email_address()` to parse email addresses from headers
   - Implemented `_decode_email_subject()` to handle encoded email subjects
   - Updated `load_results_from_folder()` to parse .eml files and extract sender info
   - Modified `open_attachment()` to actually open PDF files
   - Modified `show_in_mail()` to open .eml files
   - Changed `on_message_double_click()` to call `open_attachment()` instead of `show_in_mail()`
   - Removed "Pobierz" button and `download_attachment()` method
   - Added necessary imports: `subprocess`, `sys`, `tempfile`, `email`

2. **poczta_faktury.py**
   - Modified `_search_with_imap_threaded()` to save .eml files alongside PDFs
   - Modified `_search_with_pop3_threaded()` to save .eml files alongside PDFs
   - .eml files are saved with naming pattern `N_email.eml` to match `N_*.pdf`
   - Email timestamps are preserved on .eml files

### Metadata Structure

Each tree item has associated metadata stored in `item_metadata` dict:

```python
{
    'pdf_paths': ['/path/to/file.pdf'],      # List of PDF attachment paths
    'eml_path': '/path/to/email.eml',        # Path to complete email message
    'from_address': 'sender@example.com',    # Extracted email address
    'subject': 'Invoice #123'                # Email subject
}
```

This allows efficient retrieval of file paths when buttons are clicked without reparsing files.
