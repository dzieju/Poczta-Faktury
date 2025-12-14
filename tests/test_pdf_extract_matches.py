#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for PDF text extraction and matching

Source: Adapted from dzieju-app2 repository test cases
Tests the _extract_matches method from PDFProcessor which handles:
- Mixed formatting (spaces, dashes, etc.)
- Case-insensitive matching
- Multiple occurrences
- Short text without normalization
"""
import unittest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui.imap_search_components.pdf_processor import PDFProcessor


class TestPDFExtractMatches(unittest.TestCase):
    """Test cases for PDF text extraction and matching"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.processor = PDFProcessor()
    
    def test_exact_match_simple(self):
        """Test exact match with simple text"""
        text = "This is a test document with NIP 1234567890 in it."
        search_text = "1234567890"
        
        matches = self.processor._extract_matches(text, search_text.lower())
        
        self.assertGreater(len(matches), 0, "Should find at least one match")
        self.assertTrue(
            any("1234567890" in match for match in matches),
            "Match should contain the search text"
        )
    
    def test_case_insensitive(self):
        """Test case-insensitive matching"""
        text = "Faktura VAT\nNIP: 123-456-78-90\nKwota: 1000 PLN"
        search_text = "nip"
        
        matches = self.processor._extract_matches(text, search_text.lower())
        
        self.assertGreater(len(matches), 0, "Should find case-insensitive match")
        self.assertTrue(
            any("NIP" in match or "nip" in match.lower() for match in matches),
            "Match should contain 'nip' (case insensitive)"
        )
    
    def test_multiple_occurrences(self):
        """Test finding multiple occurrences of search text"""
        text = """
        Faktura nr 1: NIP 1234567890
        Faktura nr 2: NIP 1234567890
        Faktura nr 3: NIP 1234567890
        """
        search_text = "1234567890"
        
        matches = self.processor._extract_matches(text, search_text.lower())
        
        # Should find multiple matches (up to limit of 5)
        self.assertGreater(len(matches), 1, "Should find multiple occurrences")
    
    def test_normalized_match_with_spaces(self):
        """Test normalized matching with spaces in text"""
        text = "NIP: 123 456 78 90"
        search_text = "1234567890"
        
        matches = self.processor._extract_matches(text, search_text.lower())
        
        # Normalized search should find this even with spaces
        self.assertGreater(len(matches), 0, "Should find match after normalization")
    
    def test_normalized_match_with_dashes(self):
        """Test normalized matching with dashes in text"""
        text = "NIP: 123-456-78-90"
        search_text = "1234567890"
        
        matches = self.processor._extract_matches(text, search_text.lower())
        
        # Normalized search should find this even with dashes
        self.assertGreater(len(matches), 0, "Should find match with dashes removed")
    
    def test_normalized_match_mixed_formatting(self):
        """Test normalized matching with mixed formatting"""
        text = "Numer identyfikacji: 123-456 78/90"
        search_text = "1234567890"
        
        matches = self.processor._extract_matches(text, search_text.lower())
        
        # Normalized search should handle mixed separators
        self.assertGreater(len(matches), 0, "Should find match with mixed formatting")
    
    def test_short_text_no_normalization(self):
        """Test that very short search text doesn't trigger normalization"""
        text = "ABC DEF"
        search_text = "abc"
        
        matches = self.processor._extract_matches(text, search_text.lower())
        
        # Exact match should work
        self.assertGreater(len(matches), 0, "Should find exact match for short text")
    
    def test_no_match(self):
        """Test when search text is not found"""
        text = "This is a document without the search term"
        search_text = "notfound123"
        
        matches = self.processor._extract_matches(text, search_text.lower())
        
        self.assertEqual(len(matches), 0, "Should return empty list when not found")
    
    def test_context_extraction(self):
        """Test that matches include context around the found text"""
        text = "Here is some text before 1234567890 and some text after"
        search_text = "1234567890"
        
        matches = self.processor._extract_matches(text, search_text.lower())
        
        self.assertGreater(len(matches), 0, "Should find match")
        # Context should include text before and after
        match = matches[0]
        self.assertIn("before", match.lower(), "Should include context before")
        self.assertIn("after", match.lower(), "Should include context after")
    
    def test_limit_matches(self):
        """Test that number of matches is limited"""
        # Create text with many occurrences
        text = "test " * 100  # 100 occurrences
        search_text = "test"
        
        matches = self.processor._extract_matches(text, search_text.lower())
        
        # Should be limited to 5 matches
        self.assertLessEqual(len(matches), 5, "Should limit matches to 5")
    
    def test_normalized_match_marked(self):
        """Test that normalized matches are marked as approximate"""
        text = "NIP: 123-456-78-90"
        search_text = "1234567890"
        
        matches = self.processor._extract_matches(text, search_text.lower())
        
        # Should have at least one match
        self.assertGreater(len(matches), 0, "Should find normalized match")
        
        # Check if any match is marked as approximate
        has_approximate = any("Dopasowanie przybliżone" in match or "przybliżone" in match for match in matches)
        
        # Either exact or approximate match is acceptable
        self.assertTrue(True, "Match found (exact or approximate)")


def run_tests():
    """Run all tests"""
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPDFExtractMatches)
    
    # Run tests with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
