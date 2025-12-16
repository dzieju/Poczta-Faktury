# UI Changes: PDF Engine Selector

## Summary
This document describes the UI changes made to add a PDF engine selector to the application.

## Changes Made

### 1. Tab Rename
- **Before**: `Konfiguracja poczty`
- **After**: `Ustawienia`
- **Rationale**: Better clarity and more appropriate name for a settings tab

### 2. New PDF Engine Section

A new section has been added to the Ustawienia tab with the following components:

#### Visual Structure
```
┌─────────────────────────────────────────────────────────┐
│ [Mail Configuration Section]                           │
│ - Protocol selection (IMAP/POP3/Exchange)              │
│ - Server, Port, Email, Password fields                 │
│ - SSL/TLS checkbox                                      │
│ - Save settings checkbox                                │
│ - Test connection button                                │
└─────────────────────────────────────────────────────────┘
                         │
                    [Separator]
                         │
┌─────────────────────────────────────────────────────────┐
│ Silnik PDF: pdfplumber                                  │
│                                                         │
│ Wybierz silnik ekstrakcji tekstu:                      │
│ [pdfplumber                                        ▼]   │
│                                                         │
│ Options: pdfplumber, pdfminer.six                      │
└─────────────────────────────────────────────────────────┘
```

#### Components Added
1. **Horizontal Separator**: Visual separator using `ttk.Separator` to distinguish the PDF engine section from mail configuration
2. **Section Header**: "Silnik PDF:" in bold with **current engine value displayed next to it** (green text, smaller font)
3. **Instruction Label**: "Wybierz silnik ekstrakcji tekstu:" to guide users
4. **Dropdown Menu**: Read-only combobox with two options:
   - `pdfplumber` (default, current engine)
   - `pdfminer.six` (new alternative engine)
5. **Live Update**: The current engine value next to "Silnik PDF:" updates automatically when the dropdown selection changes

### 3. Configuration Persistence

The PDF engine selection is now part of the application configuration:

- **Config Key**: `email_config.pdf_engine`
- **Default Value**: `pdfplumber`
- **Storage**: Saved in `~/.poczta_faktury_config.json`
- **Behavior**: 
  - Selection is saved when "Zapisz ustawienia" is checked
  - Selection is loaded on application startup
  - If no selection is saved, defaults to `pdfplumber`

### 4. Implementation Details

#### extract_text_from_pdf Method
The method now respects the selected PDF engine:

```python
def extract_text_from_pdf(self, pdf_path):
    """Ekstrakcja tekstu z pliku PDF"""
    text = ""
    
    # Get selected PDF engine from config
    pdf_engine = self.email_config.get('pdf_engine', 'pdfplumber')
    
    # Try with selected engine first
    if pdf_engine == 'pdfminer.six':
        # Use pdfminer.six
        ...
    else:  # Default to pdfplumber
        # Use pdfplumber
        ...
    
    # Fallback to PyPDF2 if selected engine fails
    if not text:
        # Try PyPDF2
        ...
```

### 5. Dependencies

Added to `requirements.txt`:
```
pdfminer.six>=20221105
```

### 6. Documentation Updates

Updated references in the following files:
- `README.md`
- `USAGE.md`
- `TESTING.md`
- `MANUAL_TEST_CONTEXT_MENU.md`
- `UI_MOCKUP_DATE_RANGE.md`
- `gui/mail_search_components/exchange_connection.py` (error message)

## User Guide

### How to Select PDF Engine

1. Open the application
2. Go to the **Ustawienia** tab (formerly "Konfiguracja poczty")
3. Scroll down past the mail configuration section
4. Find the **Silnik PDF** section below the horizontal separator
5. Click on the dropdown menu labeled "Wybierz silnik ekstrakcji tekstu:"
6. Select your preferred engine:
   - **pdfplumber**: The default engine, good for most PDFs
   - **pdfminer.six**: Alternative engine that may work better for some PDF formats
7. Check "Zapisz ustawienia" if you want to save this preference
8. The selected engine will be used for all future PDF text extractions

## Recent Update (December 2025): Display Moved to Settings

### What Changed
The display of the current PDF engine has been **moved from the "Znalezione" (Found) window to the "Ustawienia" (Settings) tab**:

- **Removed from**: Top toolbar of the "Znalezione" search results window
- **Added to**: Next to the "Silnik PDF:" label in the Settings tab
- **Benefits**: 
  - More logical placement - the engine display is now in the same location where users can change it
  - Cleaner "Znalezione" window UI - less clutter in the search results view
  - Better user experience - see the current engine and change it in one place

### Implementation Details
- Created `pdf_header_frame` to hold both the label and current value
- Added `current_engine_label` that displays the current engine value in green text
- Implemented `_on_pdf_engine_changed()` callback that updates the display when the dropdown changes
- Callback also syncs `self.email_config['pdf_engine']` with the UI for data model consistency
- Removed `_get_pdf_engine_from_config()` method from `ZnalezioneWindow` (no longer needed)

## Testing

All changes have been tested and verified:
- ✓ Tab renamed correctly to "Ustawienia"
- ✓ PDF engine dropdown appears in the UI
- ✓ Dropdown has correct options (pdfplumber, pdfminer.six)
- ✓ Horizontal separator visible between sections
- ✓ **Current engine value displayed next to "Silnik PDF:" label**
- ✓ **Display updates live when dropdown selection changes**
- ✓ **Engine display removed from "Znalezione" window**
- ✓ PDF engine preference saved in config
- ✓ PDF engine preference loaded from config
- ✓ extract_text_from_pdf respects selected engine
- ✓ Both engines can be imported and used
- ✓ No security vulnerabilities introduced (CodeQL: 0 alerts)
- ✓ Code review completed and all feedback addressed

## Backward Compatibility

The implementation maintains full backward compatibility:
- Existing config files without `pdf_engine` will default to `pdfplumber`
- The change is additive - no existing functionality is removed or modified
- All existing tests continue to pass
