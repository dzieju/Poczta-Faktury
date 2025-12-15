#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test that the import fix for EmailInvoiceFinderApp works correctly
"""

import sys
import unittest
import inspect
from unittest.mock import MagicMock

# Mock tkinter and other GUI dependencies before importing
sys.modules['tkinter'] = MagicMock()
sys.modules['tkinter.ttk'] = MagicMock()
sys.modules['tkinter.messagebox'] = MagicMock()
sys.modules['tkinter.filedialog'] = MagicMock()
sys.modules['tkinter.scrolledtext'] = MagicMock()

# Mock other dependencies that might not be available
sys.modules['PyPDF2'] = MagicMock()
sys.modules['pdfplumber'] = MagicMock()


class TestImportFix(unittest.TestCase):
    """Test that the import mechanism for EmailInvoiceFinderApp works"""

    def test_import_emailinvoicefinderapp(self):
        """Test that we can import EmailInvoiceFinderApp from poczta_faktury package"""
        try:
            from poczta_faktury import EmailInvoiceFinderApp
            
            # Verify the import succeeded
            self.assertIsNotNone(EmailInvoiceFinderApp, 
                "EmailInvoiceFinderApp should not be None")
            
            # Verify it's a class
            self.assertTrue(inspect.isclass(EmailInvoiceFinderApp),
                "EmailInvoiceFinderApp should be a class")
            
            # Verify the class name
            self.assertEqual(EmailInvoiceFinderApp.__name__, "EmailInvoiceFinderApp",
                "Class name should be EmailInvoiceFinderApp")
            
            print("✓ Import test passed: from poczta_faktury import EmailInvoiceFinderApp")
            
        except ImportError as e:
            self.fail(f"Failed to import EmailInvoiceFinderApp: {e}")

    def test_import_in_all(self):
        """Test that EmailInvoiceFinderApp is in __all__"""
        import poczta_faktury
        
        self.assertIn("EmailInvoiceFinderApp", poczta_faktury.__all__,
            "EmailInvoiceFinderApp should be in __all__")
        
        print("✓ __all__ test passed: EmailInvoiceFinderApp is exported")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
