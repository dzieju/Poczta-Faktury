# Manual Testing Guide for Context Menu Feature

## Overview
This document provides step-by-step instructions for manually testing the right-click context menu feature in the search results window.

## Prerequisites
1. Python 3.7+ installed
2. All dependencies from `requirements.txt` installed
3. A configured email account in the application
4. At least one search completed with saved PDF and EML files

## Test Setup

### 1. Prepare Test Data
Before testing, you need search results with saved files:

```bash
# Run the application
python main.py
```

1. Configure email access in the "Ustawienia" tab
2. Go to "Wyszukiwanie NIP" tab
3. Enter a test NIP number (e.g., "1234567890")
4. Select an output folder (e.g., create a folder called "test_results")
5. Click "Szukaj faktur" to perform a search
6. Wait for the search to complete

### 2. Open the Search Results Window
1. After the search completes, click the "Znalezione ➜" button
2. The "Znalezione - Wyniki wyszukiwania" window should open
3. Verify that the table displays the found results (PDF files and metadata)

## Test Cases

### Test Case 1: Right-Click Menu Display
**Objective:** Verify that the context menu appears when right-clicking on a result item

**Steps:**
1. In the search results table, locate any result row
2. Right-click on the row (Windows/Linux) or Ctrl+Click (macOS)
3. **Expected:** A context menu should appear near the cursor

**Success Criteria:**
- ✅ Context menu appears at cursor position
- ✅ Menu contains relevant options based on available files

### Test Case 2: Open PDF from Context Menu
**Objective:** Verify that PDF files can be opened via context menu

**Steps:**
1. Right-click on a result row that has a PDF file
2. Select "Otwórz PDF" from the context menu
3. **Expected:** The PDF file should open in the system's default PDF viewer

**Success Criteria:**
- ✅ Menu shows "Otwórz PDF" option
- ✅ Clicking the option opens the correct PDF file
- ✅ PDF opens in system default application (e.g., Adobe Reader, browser)
- ✅ No error dialogs appear

**Error Case:**
- If PDF file is missing or moved:
  - ✅ Error dialog appears with file path and error message
  - ✅ Error message is clear and actionable

### Test Case 3: Open Email from Context Menu
**Objective:** Verify that EML files can be opened via context menu

**Steps:**
1. Right-click on a result row that has both PDF and EML files
2. Select "Otwórz Email" from the context menu
3. **Expected:** The EML file should open in the system's default email client

**Success Criteria:**
- ✅ Menu shows "Otwórz Email" option
- ✅ Clicking the option opens the correct EML file
- ✅ EML opens in system default email application (e.g., Outlook, Thunderbird)
- ✅ Email displays with correct sender, subject, and attachments

**Error Case:**
- If EML file is missing:
  - ✅ Error dialog appears with file path and error message
  - ✅ Error message is clear and actionable

### Test Case 4: Dynamic Menu Items
**Objective:** Verify that menu only shows options for available files

**Scenario A - Both Files Available:**
1. Right-click on a result with both PDF and EML files
2. **Expected:** Menu shows both "Otwórz PDF" and "Otwórz Email"

**Scenario B - Only PDF Available:**
1. Manually delete or rename the EML file for one result
2. Right-click on that result
3. **Expected:** Menu shows only "Otwórz PDF"

**Scenario C - No Files Available:**
1. Manually delete both PDF and EML files for one result
2. Right-click on that result
3. **Expected:** Info message appears: "Nie znaleziono plików PDF ani Email dla tej pozycji."

**Success Criteria:**
- ✅ Menu items appear/disappear based on file availability
- ✅ No errors when files are missing
- ✅ Appropriate message shown when no files available

### Test Case 5: Multi-Platform Support
**Objective:** Verify that file opening works on different platforms

**Platform-Specific Tests:**

**Windows:**
1. Right-click and open PDF
2. **Expected:** Opens with default PDF viewer (Adobe, Edge, etc.)
3. Right-click and open Email
4. **Expected:** Opens with default mail client (Outlook, Windows Mail, etc.)

**macOS:**
1. Ctrl+Click (or right-click if available) and open PDF
2. **Expected:** Opens with Preview or configured PDF viewer
3. Ctrl+Click and open Email
4. **Expected:** Opens with Mail.app or configured mail client

**Linux:**
1. Right-click and open PDF
2. **Expected:** Opens with configured PDF viewer (Evince, Okular, etc.)
3. Right-click and open Email
4. **Expected:** Opens with configured mail client (Thunderbird, Evolution, etc.)

**Success Criteria:**
- ✅ Files open correctly on the test platform
- ✅ System default applications are used
- ✅ No permission errors

### Test Case 6: Error Handling
**Objective:** Verify proper error handling and user feedback

**Test Steps:**
1. Modify a PDF file path in the output folder (rename or move it)
2. Try to open the PDF via context menu
3. **Expected:** Error dialog with:
   - Clear Polish error message
   - Full file path that was attempted
   - Specific error description

**Success Criteria:**
- ✅ Error dialog appears (not a crash)
- ✅ Error message includes file path
- ✅ Error message includes error description
- ✅ Error message is in Polish
- ✅ Application remains stable after error

### Test Case 7: Integration with Existing Buttons
**Objective:** Verify context menu works alongside existing buttons

**Steps:**
1. Select a result row by clicking on it
2. Test the "Otwórz załącznik" button - should open PDF
3. Test the "Pokaż w poczcie" button - should open EML
4. Now right-click and use context menu for the same actions
5. **Expected:** All three methods (double-click, buttons, context menu) work consistently

**Success Criteria:**
- ✅ Context menu actions produce same result as buttons
- ✅ No conflicts between different activation methods
- ✅ Row selection works correctly with right-click

### Test Case 8: Keyboard Navigation
**Objective:** Verify accessibility with keyboard

**Steps:**
1. Use Tab to navigate to the results table
2. Use arrow keys to select different results
3. Try the application menu key (≣ key on Windows keyboards)
4. **Expected:** Context menu should appear for keyboard-accessed items

**Success Criteria:**
- ✅ Context menu can be triggered via keyboard (if platform supports it)
- ✅ Menu items can be selected with arrow keys and Enter

## Test Results Template

Use this template to record your test results:

```
Test Date: _____________
Tester: ________________
Platform: Windows / macOS / Linux (circle one)
Python Version: ________

Test Case 1 - Menu Display: PASS / FAIL
Notes: _________________________________________

Test Case 2 - Open PDF: PASS / FAIL
Notes: _________________________________________

Test Case 3 - Open Email: PASS / FAIL
Notes: _________________________________________

Test Case 4 - Dynamic Items: PASS / FAIL
Notes: _________________________________________

Test Case 5 - Platform Support: PASS / FAIL
Notes: _________________________________________

Test Case 6 - Error Handling: PASS / FAIL
Notes: _________________________________________

Test Case 7 - Button Integration: PASS / FAIL
Notes: _________________________________________

Test Case 8 - Keyboard Navigation: PASS / FAIL
Notes: _________________________________________

Overall Result: PASS / FAIL
Additional Comments:
_______________________________________________
```

## Known Limitations

1. **Tkinter Display Required:** Tests cannot run in headless environments
2. **Platform Dependencies:** File opening behavior depends on OS configuration
3. **Default Applications:** Users must have PDF and email applications configured

## Troubleshooting

### Context Menu Doesn't Appear
- Check that you're right-clicking on a row (not empty space)
- On macOS, try Ctrl+Click if right-click doesn't work
- Verify tkinter is properly installed

### Files Don't Open
- Check that default applications are configured for .pdf and .eml files
- Verify file permissions (files should be readable)
- Check system PATH includes necessary application directories

### Error Messages Not Clear
- Report the exact error message text
- Note the file path shown in the error
- Check application logs for additional details
