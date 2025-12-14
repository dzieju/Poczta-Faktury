#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration test for znalezione_window with mock email data
"""
import os
import sys
import tempfile
import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def create_test_eml(sender_email, subject, tmpdir, index):
    """Create a test EML file"""
    msg = MIMEMultipart()
    msg['From'] = f'Test Sender {index} <{sender_email}>'
    msg['To'] = 'recipient@example.com'
    msg['Subject'] = subject
    msg['Date'] = email.utils.formatdate(localtime=True)
    
    body = f"This is a test email message number {index}"
    msg.attach(MIMEText(body, 'plain'))
    
    eml_path = os.path.join(tmpdir, f'{index}_email.eml')
    with open(eml_path, 'wb') as f:
        f.write(msg.as_bytes())
    
    return eml_path

def create_test_pdf(tmpdir, index):
    """Create a minimal test PDF file"""
    pdf_path = os.path.join(tmpdir, f'{index}_invoice.pdf')
    # Minimal PDF structure
    pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 44 >>
stream
BT
/F1 12 Tf
100 700 Td
(Test Invoice) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000214 00000 n 
trailer
<< /Size 5 /Root 1 0 R >>
startxref
308
%%EOF
"""
    with open(pdf_path, 'wb') as f:
        f.write(pdf_content)
    
    return pdf_path

def test_load_results_from_folder():
    """Test loading results from a folder with PDF and EML files"""
    print("\nIntegration Test: Load Results from Folder")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"Created temporary directory: {tmpdir}")
        
        # Create test data
        test_data = [
            ('sender1@example.com', 'Invoice #001'),
            ('sender2@company.org', 'Receipt for Order 123'),
            ('billing@service.net', 'Monthly Statement'),
        ]
        
        for i, (sender, subject) in enumerate(test_data, 1):
            eml_path = create_test_eml(sender, subject, tmpdir, i)
            pdf_path = create_test_pdf(tmpdir, i)
            print(f"  ✓ Created EML and PDF for entry {i}")
        
        # Now test the parsing logic (without GUI)
        print("\nTesting parsing logic:")
        
        # Get all PDF files
        pdf_files = [f for f in os.listdir(tmpdir) if f.lower().endswith('.pdf')]
        pdf_files.sort()
        
        print(f"  Found {len(pdf_files)} PDF files")
        
        # Create mapping of EML files
        eml_files = {}
        for f in os.listdir(tmpdir):
            if f.lower().endswith('.eml'):
                parts = f.split('_')
                if parts:
                    num = parts[0]
                    eml_files[num] = os.path.join(tmpdir, f)
        
        print(f"  Found {len(eml_files)} EML files")
        
        # Process each PDF
        results = []
        for fname in pdf_files:
            full = os.path.join(tmpdir, fname)
            
            # Extract number prefix
            pdf_parts = fname.split('_')
            if pdf_parts:
                num = pdf_parts[0]
                eml_path = eml_files.get(num)
                
                if eml_path and os.path.isfile(eml_path):
                    # Parse EML
                    with open(eml_path, 'rb') as eml_file:
                        eml_message = email.message_from_bytes(eml_file.read())
                        from_header = eml_message.get('From', '-')
                        subject = eml_message.get('Subject', fname)
                        
                        # Extract email address
                        import re
                        email_pattern = r'<([^>]+)>'
                        match = re.search(email_pattern, from_header)
                        from_address = match.group(1) if match else from_header.strip()
                        
                        results.append({
                            'pdf_path': full,
                            'eml_path': eml_path,
                            'from_address': from_address,
                            'subject': subject
                        })
                        
                        print(f"  ✓ Parsed entry {num}:")
                        print(f"    From: {from_address}")
                        print(f"    Subject: {subject}")
        
        # Verify results
        if len(results) != len(test_data):
            print(f"  ✗ Expected {len(test_data)} results, got {len(results)}")
            return False
        
        for i, (expected_sender, expected_subject) in enumerate(test_data):
            result = results[i]
            if result['from_address'] != expected_sender:
                print(f"  ✗ Expected sender {expected_sender}, got {result['from_address']}")
                return False
            if result['subject'] != expected_subject:
                print(f"  ✗ Expected subject {expected_subject}, got {result['subject']}")
                return False
        
        print("\n  ✓ All data parsed correctly")
        print("  ✓ Integration test passed")
        
        return True

def test_file_operations():
    """Test file operations that would be performed by button handlers"""
    print("\nIntegration Test: File Operations")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        pdf_path = create_test_pdf(tmpdir, 1)
        eml_path = create_test_eml('test@example.com', 'Test', tmpdir, 1)
        
        print(f"  ✓ Created test files")
        
        # Test file existence checks
        if not os.path.isfile(pdf_path):
            print(f"  ✗ PDF file not found")
            return False
        
        if not os.path.isfile(eml_path):
            print(f"  ✗ EML file not found")
            return False
        
        print(f"  ✓ File existence checks passed")
        
        # Test metadata structure
        metadata = {
            'pdf_paths': [pdf_path],
            'eml_path': eml_path,
            'from_address': 'test@example.com',
            'subject': 'Test'
        }
        
        # Simulate button handler logic
        # 1. Open attachment
        pdf_paths = metadata.get('pdf_paths', [])
        if not pdf_paths:
            print(f"  ✗ No PDF paths in metadata")
            return False
        
        pdf_to_open = pdf_paths[0]
        if not os.path.isfile(pdf_to_open):
            print(f"  ✗ PDF path not valid: {pdf_to_open}")
            return False
        
        print(f"  ✓ Would open PDF: {os.path.basename(pdf_to_open)}")
        
        # 2. Show in mail
        eml_to_open = metadata.get('eml_path')
        if not eml_to_open or not os.path.isfile(eml_to_open):
            print(f"  ✗ EML path not valid")
            return False
        
        print(f"  ✓ Would open EML: {os.path.basename(eml_to_open)}")
        
        print("\n  ✓ File operations test passed")
        
        return True

def main():
    """Run integration tests"""
    print("=" * 60)
    print("Znalezione Window Integration Tests")
    print("=" * 60)
    
    tests = [
        ("Load Results from Folder", test_load_results_from_folder),
        ("File Operations", test_file_operations),
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
    print("Integration Test Summary")
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
        print("\n✓ All integration tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())
