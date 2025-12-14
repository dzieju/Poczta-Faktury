# UI Changes - Search Results Window

This document describes the visual changes made to the "Znalezione - Wyniki wyszukiwania" (Search Results Window).

## Before and After Comparison

### BEFORE (Original UI)

```
┌─────────────────────────────────────────────────────────────────┐
│ Znalezione - Wyniki wyszukiwania                          [_][□][X]│
├─────────────────────────────────────────────────────────────────┤
│ [Wyniki wyszukiwania]                      [Odśwież]            │
├─────────────────────────────────────────────────────────────────┤
│ Znalezione wiadomości:                                           │
│ ┌───────────────────────────────────────────────────────────┐  │
│ │Data           │Nadawca  │Temat    │Folder │Załączniki│Status││
│ ├───────────────────────────────────────────────────────────┤  │
│ │2024-01-15 10:30│    -    │invoice.pdf│/path │    1    │Zapisano││  ← Nadawca column EMPTY
│ │2024-01-14 09:15│    -    │receipt.pdf│/path │    1    │Zapisano││  ← Nadawca column EMPTY
│ │2024-01-13 14:22│    -    │order.pdf  │/path │    1    │Zapisano││  ← Nadawca column EMPTY
│ └───────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│ Dopasowania w PDF:                                               │
│ ┌───────────────────────────────────────────────────────────┐  │
│ │                                                           │  │
│ │ Wybrana wiadomość:                                        │  │
│ │ Data: 2024-01-15 10:30                                    │  │
│ │ Od: -                                                     │  │  ← Empty sender
│ │ Temat: invoice.pdf                                        │  │
│ │                                                           │  │
│ └───────────────────────────────────────────────────────────┘  │
│                                                                   │
│ [Otwórz załącznik] [Pobierz] [Pokaż w poczcie]                  │  ← 3 buttons
│    ↑                  ↑           ↑                              │
│    Non-functional     To remove   Non-functional                │
├─────────────────────────────────────────────────────────────────┤
│ Znaleziono: 3 wiadomości          [« Poprzednia] Strona 1 [Następna »]│
└─────────────────────────────────────────────────────────────────┘
```

**Issues in original UI:**
1. ❌ "Nadawca" (Sender) column shows "-" instead of email address
2. ❌ Double-click does nothing
3. ❌ "Otwórz załącznik" button shows placeholder message
4. ❌ "Pobierz" button is redundant
5. ❌ "Pokaż w poczcie" button shows placeholder message

---

### AFTER (Enhanced UI)

```
┌─────────────────────────────────────────────────────────────────┐
│ Znalezione - Wyniki wyszukiwania                          [_][□][X]│
├─────────────────────────────────────────────────────────────────┤
│ [Wyniki wyszukiwania]                      [Odśwież]            │
├─────────────────────────────────────────────────────────────────┤
│ Znalezione wiadomości:                                           │
│ ┌───────────────────────────────────────────────────────────┐  │
│ │Data           │Nadawca            │Temat    │Folder│Załączniki│Status││
│ ├───────────────────────────────────────────────────────────┤  │
│ │2024-01-15 10:30│sender@company.com │Invoice #001│/path│ 1  │Zapisano││  ✓ Email shown
│ │2024-01-14 09:15│billing@store.org  │Receipt 123 │/path│ 1  │Zapisano││  ✓ Email shown
│ │2024-01-13 14:22│finance@acme.net   │Order PDF   │/path│ 1  │Zapisano││  ✓ Email shown
│ └───────────────────────────────────────────────────────────┘  │
│                           ↑ Double-click opens PDF               │
├─────────────────────────────────────────────────────────────────┤
│ Dopasowania w PDF:                                               │
│ ┌───────────────────────────────────────────────────────────┐  │
│ │                                                           │  │
│ │ Wybrana wiadomość:                                        │  │
│ │ Data: 2024-01-15 10:30                                    │  │
│ │ Od: sender@company.com                    ← Email shown! │  │
│ │ Temat: Invoice #001                       ← Real subject │  │
│ │                                                           │  │
│ └───────────────────────────────────────────────────────────┘  │
│                                                                   │
│ [Otwórz załącznik] [Pokaż w poczcie]                            │  ← 2 buttons only
│    ↑                   ↑                                         │
│    Opens PDF in        Opens .eml in email                      │
│    system PDF viewer   client (Outlook, etc.)                   │
├─────────────────────────────────────────────────────────────────┤
│ Znaleziono: 3 plików              [« Poprzednia] Strona 1 [Następna »]│
└─────────────────────────────────────────────────────────────────┘
```

**Improvements in new UI:**
1. ✅ "Nadawca" (Sender) column displays actual email addresses (e.g., sender@company.com)
2. ✅ Double-click on any row opens the PDF attachment
3. ✅ "Otwórz załącznik" button opens PDF in system default viewer
4. ✅ "Pobierz" button removed (streamlined UI)
5. ✅ "Pokaż w poczcie" button opens complete email (.eml file)
6. ✅ Subject shows actual email subject, not just filename
7. ✅ Better error handling with informative messages

## Detailed Changes

### 1. Sender Column Population

**Before:**
- Column always showed "-" (dash)
- No email information available

**After:**
- Extracts email address from .eml file's "From" header
- Handles various formats:
  - `sender@example.com`
  - `"John Doe" <john@example.com>` → extracts `john@example.com`
  - Encoded headers are properly decoded

**Implementation:**
```python
# Parses EML file and extracts clean email address
from_header = email_message.get('From', '-')
from_address = self._extract_email_address(from_header)
```

### 2. Double-Click Functionality

**Before:**
- Double-click called `show_in_mail()` (which did nothing)

**After:**
- Double-click calls `open_attachment()` (opens PDF)
- User can quickly open PDFs by double-clicking rows
- Consistent with typical file browser behavior

### 3. Button Layout

**Before:**
```
[Otwórz załącznik]  [Pobierz]  [Pokaż w poczcie]
```

**After:**
```
[Otwórz załącznik]  [Pokaż w poczcie]
```

The "Pobierz" (Download) button was removed because:
- Files are already downloaded to the output folder
- The button was redundant with "Otwórz załącznik"
- Simpler UI is more intuitive

### 4. File Opening Mechanism

#### PDF Files (Otwórz załącznik)
**Before:**
- Showed placeholder message: "Funkcja otwierania załącznika zostanie zaimplementowana"

**After:**
- Opens PDF in system default application
- Cross-platform support:
  - **Windows**: `os.startfile()`
  - **macOS**: `subprocess.run(['open', file])`
  - **Linux**: `subprocess.run(['xdg-open', file])`
- Error handling:
  - File not found
  - No default application
  - Permission errors

#### EML Files (Pokaż w poczcie)
**Before:**
- Showed placeholder message: "Funkcja pokazania w kliencie pocztowym zostanie zaimplementowana"

**After:**
- Opens complete email message (.eml file) in default email client
- Shows full email with:
  - Headers (From, To, Date, Subject)
  - Message body
  - All attachments (not just PDFs)
- Works with common email clients:
  - **Windows**: Outlook, Windows Mail
  - **macOS**: Mail.app
  - **Linux**: Thunderbird, Evolution

### 5. Error Messages

The UI now provides informative error messages:

**No PDF Found:**
```
⚠ Ostrzeżenie
Nie znaleziono ścieżki do załącznika PDF
```

**No EML Found:**
```
⚠ Ostrzeżenie
Plik .eml nie jest dostępny.

Ta funkcja działa tylko gdy wiadomości są zapisane jako pliki .eml na dysku.
```

**File Opening Error:**
```
✗ Błąd
Nie udało się otworzyć załącznika:
[detailed error message]
```

## Data Flow

### Search Process with EML Saving

```
1. User initiates search
   ↓
2. Application connects to email server (IMAP/POP3)
   ↓
3. For each email with matching PDF:
   ├─→ Save PDF as: N_filename.pdf
   └─→ Save EML as: N_email.eml  ← NEW!
   ↓
4. User clicks "Znalezione" button
   ↓
5. Search Results Window loads:
   ├─→ Scans folder for PDF files
   ├─→ Matches PDFs to EML files by number prefix
   ├─→ Parses EML files to extract:
   │   ├─→ From email address
   │   └─→ Subject
   └─→ Populates table with extracted data
   ↓
6. User interactions:
   ├─→ Double-click row → Opens PDF
   ├─→ "Otwórz załącznik" → Opens PDF
   └─→ "Pokaż w poczcie" → Opens EML
```

### File Structure

After search, the output folder contains paired files:

```
output_folder/
├── 1_invoice.pdf         ← PDF attachment
├── 1_email.eml           ← Complete email (NEW!)
├── 2_receipt.pdf         ← PDF attachment
├── 2_email.eml           ← Complete email (NEW!)
└── ...
```

The number prefix (1_, 2_, etc.) links PDFs to their source emails.

## User Experience Improvements

### Before This Update
1. User had to manually locate and open PDF files from file explorer
2. No way to see original email context
3. No sender information visible
4. Three buttons but only one worked
5. Confusing UI

### After This Update
1. ✅ Quick access: Double-click to open PDF
2. ✅ Context available: Click "Pokaż w poczcie" to see full email
3. ✅ Sender visible at a glance in results table
4. ✅ Streamlined: Two working buttons, clear purpose
5. ✅ Intuitive: Behaves like standard file/email applications

## Technical Implementation Notes

### Cross-Platform Compatibility

The file opening logic automatically detects the platform:

```python
def _open_file_with_system_app(self, file_path):
    if sys.platform == 'win32':
        os.startfile(file_path)           # Windows
    elif sys.platform == 'darwin':
        subprocess.run(['open', file_path])  # macOS
    else:
        subprocess.run(['xdg-open', file_path])  # Linux
```

### Metadata Storage

Each row in the tree has associated metadata:

```python
metadata = {
    'pdf_paths': ['/full/path/to/1_invoice.pdf'],
    'eml_path': '/full/path/to/1_email.eml',
    'from_address': 'sender@example.com',
    'subject': 'Invoice #001'
}
```

This avoids re-parsing files when buttons are clicked.

### Email Parsing

Uses Python's built-in `email` module:

```python
with open(eml_path, 'rb') as f:
    eml_message = email.message_from_bytes(f.read())
    from_header = eml_message.get('From')
    subject = eml_message.get('Subject')
```

Handles:
- Encoded headers (=?utf-8?Q?...?=)
- Multiple address formats
- Missing headers gracefully

## Backwards Compatibility

### Old Search Results (Before Update)
- PDFs exist: ✅ Will be displayed
- EML files: ❌ Don't exist (created by old version)
- "Nadawca" column: Shows "-" (no EML to parse)
- "Otwórz załącznik": ✅ Still works (opens PDF)
- "Pokaż w poczcie": Shows message "Plik .eml nie jest dostępny"

### New Search Results (After Update)
- PDFs exist: ✅ Created during search
- EML files: ✅ Created during search (NEW!)
- "Nadawca" column: ✅ Shows email address
- "Otwórz załącznik": ✅ Opens PDF
- "Pokaż w poczcie": ✅ Opens EML

**Recommendation:** Re-run searches to get full functionality with email addresses and .eml files.
