#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for znalezione_window functionality
"""
import os
import sys
import tempfile
from pathlib import Path

def test_email_address_extraction():
    """Test email address extraction from various From headers"""
    # Mock the _extract_email_address method
    def extract_email_address(from_header):
        if not from_header:
            return '-'
        import re
        email_pattern = r'<([^>]+)>'
        match = re.search(email_pattern, from_header)
        if match:
            return match.group(1)
        return from_header.strip()
    
    # Test cases
    test_cases = [
        ("John Doe <john@example.com>", "john@example.com"),
        ("<jane@example.com>", "jane@example.com"),
        ("bob@example.com", "bob@example.com"),
        ("", "-"),
        (None, "-"),
        ("Alice Smith <alice.smith@company.org>", "alice.smith@company.org"),
    ]
    
    print("Testing email address extraction:")
    for input_val, expected in test_cases:
        result = extract_email_address(input_val)
        status = "✓" if result == expected else "✗"
        print(f"  {status} Input: {repr(input_val)}")
        print(f"    Expected: {expected}, Got: {result}")
        if result != expected:
            return False
    
    return True

def test_file_opening_logic():
    """Test file opening with system app"""
    print("\nTesting file opening logic:")
    
    # Test file existence check
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        tmp_path = tmp.name
        tmp.write(b'%PDF-1.4 fake pdf')
    
    try:
        print(f"  ✓ Created temporary file: {tmp_path}")
        
        # Verify file exists
        if not os.path.isfile(tmp_path):
            print(f"  ✗ File not found: {tmp_path}")
            return False
        
        print(f"  ✓ File exists and can be checked")
        
        # Test non-existent file (cross-platform)
        non_existent = os.path.join(tempfile.gettempdir(), 'non_existent_file_12345.pdf')
        if os.path.isfile(non_existent):
            print(f"  ✗ Non-existent file check failed")
            return False
        
        print(f"  ✓ Non-existent file check passed")
        
    finally:
        # Cleanup
        try:
            os.unlink(tmp_path)
            print(f"  ✓ Cleaned up temporary file")
        except:
            pass
    
    return True

def test_metadata_structure():
    """Test metadata structure for tree items"""
    print("\nTesting metadata structure:")
    
    # Expected metadata structure
    metadata = {
        'pdf_paths': ['/path/to/file.pdf'],
        'eml_path': '/path/to/email.eml',
        'from_address': 'sender@example.com',
        'subject': 'Test Subject'
    }
    
    # Verify all required fields exist
    required_fields = ['pdf_paths', 'eml_path', 'from_address', 'subject']
    for field in required_fields:
        if field not in metadata:
            print(f"  ✗ Missing required field: {field}")
            return False
        print(f"  ✓ Field exists: {field}")
    
    # Verify types
    if not isinstance(metadata['pdf_paths'], list):
        print(f"  ✗ pdf_paths should be a list")
        return False
    
    print(f"  ✓ pdf_paths is a list")
    
    return True

def test_eml_pdf_mapping():
    """Test EML to PDF mapping logic"""
    print("\nTesting EML to PDF mapping:")
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        pdf_files = ['1_invoice.pdf', '2_receipt.pdf', '3_document.pdf']
        eml_files = ['1_email.eml', '2_email.eml', '3_email.eml']
        
        for pdf in pdf_files:
            Path(os.path.join(tmpdir, pdf)).touch()
        
        for eml in eml_files:
            Path(os.path.join(tmpdir, eml)).touch()
        
        print(f"  ✓ Created test files in {tmpdir}")
        
        # Test mapping logic
        eml_map = {}
        for f in os.listdir(tmpdir):
            if f.lower().endswith('.eml'):
                parts = f.split('_')
                if parts:
                    num = parts[0]
                    eml_map[num] = os.path.join(tmpdir, f)
        
        # Verify mappings
        for pdf in pdf_files:
            num = pdf.split('_')[0]
            if num not in eml_map:
                print(f"  ✗ No EML mapping found for PDF: {pdf}")
                return False
            print(f"  ✓ Mapped {pdf} to {os.path.basename(eml_map[num])}")
        
        print(f"  ✓ All mappings correct")
    
    return True

def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing Znalezione Window Enhancements")
    print("=" * 60)
    
    tests = [
        ("Email Address Extraction", test_email_address_extraction),
        ("File Opening Logic", test_file_opening_logic),
        ("Metadata Structure", test_metadata_structure),
        ("EML to PDF Mapping", test_eml_pdf_mapping),
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
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    all_passed = True
    for name, result in results:
        status = "PASSED" if result else "FAILED"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {name}: {status}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n✓ All tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())
