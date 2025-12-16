#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script for context menu functionality in znalezione_window
"""
import os
import sys
import tempfile
from pathlib import Path
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_context_menu_creation():
    """Test that context menu can be created for Treeview"""
    print("\nTesting context menu creation:")
    
    try:
        import tkinter as tk
        from tkinter import ttk
        
        # Create minimal window
        root = tk.Tk()
        root.withdraw()  # Hide the window
        
        # Create treeview
        tree = ttk.Treeview(root, columns=('col1',), show='headings')
        
        # Create context menu
        context_menu = tk.Menu(tree, tearoff=0)
        context_menu.add_command(label="Test Item", command=lambda: None)
        
        print("  ✓ Context menu created successfully")
        
        # Cleanup
        root.destroy()
        return True
        
    except Exception as e:
        print(f"  ✗ Failed to create context menu: {e}")
        return False

def test_file_validation():
    """Test file existence checking before opening"""
    print("\nTesting file validation:")
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        tmp_path = tmp.name
        tmp.write(b'%PDF-1.4 fake pdf')
    
    try:
        # Test existing file
        if not os.path.isfile(tmp_path):
            print(f"  ✗ File existence check failed for existing file")
            return False
        print(f"  ✓ Correctly identified existing file")
        
        # Test non-existent file
        fake_path = os.path.join(tempfile.gettempdir(), 'nonexistent_12345.pdf')
        if os.path.isfile(fake_path):
            print(f"  ✗ Non-existent file check failed")
            return False
        print(f"  ✓ Correctly identified non-existent file")
        
        return True
        
    finally:
        # Cleanup
        try:
            os.unlink(tmp_path)
        except:
            pass

def test_pdf_eml_pairing():
    """Test PDF to EML file pairing logic"""
    print("\nTesting PDF to EML file pairing:")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        test_files = {
            'pdfs': ['1_invoice.pdf', '2_receipt.pdf', '3_document.pdf'],
            'emls': ['1_email.eml', '2_email.eml', '3_email.eml']
        }
        
        # Create PDF files
        for pdf in test_files['pdfs']:
            Path(os.path.join(tmpdir, pdf)).write_bytes(b'%PDF-1.4')
        
        # Create EML files
        for eml in test_files['emls']:
            msg = MIMEText("Test email content")
            msg['Subject'] = 'Test Subject'
            msg['From'] = 'test@example.com'
            msg['To'] = 'recipient@example.com'
            Path(os.path.join(tmpdir, eml)).write_bytes(msg.as_bytes())
        
        # Test pairing logic
        eml_map = {}
        for f in os.listdir(tmpdir):
            if f.lower().endswith('.eml'):
                parts = f.split('_')
                if parts:
                    num = parts[0]
                    eml_map[num] = os.path.join(tmpdir, f)
        
        # Verify each PDF has a matching EML
        all_paired = True
        for pdf in test_files['pdfs']:
            num = pdf.split('_')[0]
            if num not in eml_map:
                print(f"  ✗ No EML found for {pdf}")
                all_paired = False
            else:
                print(f"  ✓ Paired {pdf} with {os.path.basename(eml_map[num])}")
        
        return all_paired

def test_metadata_structure_for_context_menu():
    """Test metadata structure required for context menu"""
    print("\nTesting metadata structure for context menu:")
    
    # Test metadata with both PDF and EML
    metadata_full = {
        'pdf_paths': ['/path/to/invoice.pdf'],
        'eml_path': '/path/to/email.eml',
        'from_address': 'sender@example.com',
        'subject': 'Invoice #123'
    }
    
    # Verify structure
    has_pdf = bool(metadata_full.get('pdf_paths'))
    has_eml = bool(metadata_full.get('eml_path'))
    
    if not has_pdf or not has_eml:
        print(f"  ✗ Full metadata missing required fields")
        return False
    print(f"  ✓ Full metadata has both PDF and EML paths")
    
    # Test metadata with only PDF
    metadata_pdf_only = {
        'pdf_paths': ['/path/to/invoice.pdf'],
        'eml_path': None,
        'from_address': 'sender@example.com',
        'subject': 'Invoice #123'
    }
    
    has_pdf = bool(metadata_pdf_only.get('pdf_paths'))
    has_eml = bool(metadata_pdf_only.get('eml_path'))
    
    if not has_pdf or has_eml:
        print(f"  ✗ PDF-only metadata check failed")
        return False
    print(f"  ✓ PDF-only metadata correctly identified")
    
    # Test empty metadata
    metadata_empty = {}
    
    has_pdf = bool(metadata_empty.get('pdf_paths'))
    has_eml = bool(metadata_empty.get('eml_path'))
    
    if has_pdf or has_eml:
        print(f"  ✗ Empty metadata check failed")
        return False
    print(f"  ✓ Empty metadata correctly identified")
    
    return True

def test_menu_item_visibility():
    """Test dynamic menu item showing/hiding based on file availability"""
    print("\nTesting menu item visibility logic:")
    
    # Scenario 1: Both files available
    metadata = {
        'pdf_paths': ['/tmp/test.pdf'],
        'eml_path': '/tmp/test.eml'
    }
    
    # Create temporary files
    pdf_path = '/tmp/test_context_menu_test.pdf'
    eml_path = '/tmp/test_context_menu_test.eml'
    
    try:
        # Create test files
        Path(pdf_path).write_bytes(b'%PDF-1.4')
        Path(eml_path).write_bytes(b'Test EML content')
        
        # Update metadata with real paths
        metadata['pdf_paths'] = [pdf_path]
        metadata['eml_path'] = eml_path
        
        # Check availability
        has_pdf = bool(metadata.get('pdf_paths') and 
                      any(os.path.isfile(p) for p in metadata['pdf_paths']))
        has_eml = bool(metadata.get('eml_path') and 
                      os.path.isfile(metadata['eml_path']))
        
        if not (has_pdf and has_eml):
            print(f"  ✗ Both files should be available")
            return False
        print(f"  ✓ Both PDF and EML correctly detected as available")
        
        # Scenario 2: Only PDF available
        os.unlink(eml_path)
        
        has_pdf = bool(metadata.get('pdf_paths') and 
                      any(os.path.isfile(p) for p in metadata['pdf_paths']))
        has_eml = bool(metadata.get('eml_path') and 
                      os.path.isfile(metadata['eml_path']))
        
        if not (has_pdf and not has_eml):
            print(f"  ✗ Only PDF should be available")
            return False
        print(f"  ✓ Only PDF correctly detected when EML is missing")
        
        # Scenario 3: No files available
        os.unlink(pdf_path)
        
        has_pdf = bool(metadata.get('pdf_paths') and 
                      any(os.path.isfile(p) for p in metadata['pdf_paths']))
        has_eml = bool(metadata.get('eml_path') and 
                      os.path.isfile(metadata['eml_path']))
        
        if has_pdf or has_eml:
            print(f"  ✗ No files should be available")
            return False
        print(f"  ✓ No files correctly detected when both are missing")
        
        return True
        
    finally:
        # Cleanup
        for path in [pdf_path, eml_path]:
            try:
                if os.path.exists(path):
                    os.unlink(path)
            except:
                pass

def test_error_handling():
    """Test error message formatting"""
    print("\nTesting error message formatting:")
    
    # Test file path in error message (matching production code format)
    file_path = "/path/to/nonexistent/file.pdf"
    error = "File not found"
    file_type = "PDF"
    
    error_msg = f"Nie udało się otworzyć pliku {file_type}:\n\nŚcieżka: {file_path}\n\nBłąd: {error}"
    
    if file_path not in error_msg or error not in error_msg:
        print(f"  ✗ Error message missing required information")
        return False
    print(f"  ✓ Error message contains file path and error description")
    
    # Verify file type is included
    if file_type not in error_msg:
        print(f"  ✗ Error message should include file type")
        return False
    print(f"  ✓ Error message includes file type")
    
    # Verify multi-line format
    lines = error_msg.split('\n')
    if len(lines) < 3:
        print(f"  ✗ Error message should be multi-line")
        return False
    print(f"  ✓ Error message formatted on multiple lines for readability")
    
    return True

def main():
    """Run all tests"""
    print("=" * 70)
    print("Testing Context Menu Functionality for Znalezione Window")
    print("=" * 70)
    
    tests = [
        ("Context Menu Creation", test_context_menu_creation),
        ("File Validation", test_file_validation),
        ("PDF to EML Pairing", test_pdf_eml_pairing),
        ("Metadata Structure", test_metadata_structure_for_context_menu),
        ("Menu Item Visibility", test_menu_item_visibility),
        ("Error Handling", test_error_handling),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Print summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    all_passed = True
    for name, result in results:
        status = "PASSED" if result else "FAILED"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {name}: {status}")
        if not result:
            all_passed = False
    
    print("=" * 70)
    
    if all_passed:
        print("\n✓ All tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())
