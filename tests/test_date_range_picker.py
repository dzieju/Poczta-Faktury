#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for date range picker functionality in the NIP search tab.

Tests the date range validation and filtering logic for custom date ranges.
"""
import pytest
from datetime import datetime, timedelta, date
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestDateRangeValidation:
    """Test cases for date range validation"""
    
    def test_no_date_range_is_valid(self):
        """Test that having no date range (both None) is valid"""
        # Mock app instance with validation method
        from poczta_faktury import EmailInvoiceFinderApp
        
        with patch('tkinter.Tk'):
            app = EmailInvoiceFinderApp(Mock())
            app.date_from_entry = None
            app.date_to_entry = None
            
            is_valid, date_from, date_to, error = app.validate_date_range()
            
            assert is_valid is True
            assert date_from is None
            assert date_to is None
            assert error == ""
    
    def test_valid_date_range(self):
        """Test that a valid date range (from < to) passes validation"""
        from poczta_faktury import EmailInvoiceFinderApp
        
        with patch('tkinter.Tk'):
            app = EmailInvoiceFinderApp(Mock())
            
            # Mock date entry widgets
            mock_from = Mock()
            mock_from.get.return_value = "2025-01-01"
            mock_from.get_date.return_value = date(2025, 1, 1)
            
            mock_to = Mock()
            mock_to.get.return_value = "2025-12-31"
            mock_to.get_date.return_value = date(2025, 12, 31)
            
            app.date_from_entry = mock_from
            app.date_to_entry = mock_to
            
            is_valid, date_from, date_to, error = app.validate_date_range()
            
            assert is_valid is True
            assert date_from == date(2025, 1, 1)
            assert date_to == date(2025, 12, 31)
            assert error == ""
    
    def test_invalid_date_range_from_after_to(self):
        """Test that date range with from > to fails validation"""
        from poczta_faktury import EmailInvoiceFinderApp
        
        with patch('tkinter.Tk'):
            app = EmailInvoiceFinderApp(Mock())
            
            # Mock date entry widgets with invalid range
            mock_from = Mock()
            mock_from.get.return_value = "2025-12-31"
            mock_from.get_date.return_value = date(2025, 12, 31)
            
            mock_to = Mock()
            mock_to.get.return_value = "2025-01-01"
            mock_to.get_date.return_value = date(2025, 1, 1)
            
            app.date_from_entry = mock_from
            app.date_to_entry = mock_to
            
            is_valid, date_from, date_to, error = app.validate_date_range()
            
            assert is_valid is False
            assert "późniejsza" in error.lower() or "późniejsza" in error
    
    def test_only_from_date(self):
        """Test that having only from date is valid (search from date to end)"""
        from poczta_faktury import EmailInvoiceFinderApp
        
        with patch('tkinter.Tk'):
            app = EmailInvoiceFinderApp(Mock())
            
            # Mock date entry widgets
            mock_from = Mock()
            mock_from.get.return_value = "2025-01-01"
            mock_from.get_date.return_value = date(2025, 1, 1)
            
            mock_to = Mock()
            mock_to.get.return_value = ""  # Empty
            
            app.date_from_entry = mock_from
            app.date_to_entry = mock_to
            
            is_valid, date_from, date_to, error = app.validate_date_range()
            
            assert is_valid is True
            assert date_from == date(2025, 1, 1)
            assert date_to is None
    
    def test_only_to_date(self):
        """Test that having only to date is valid (search from beginning to date)"""
        from poczta_faktury import EmailInvoiceFinderApp
        
        with patch('tkinter.Tk'):
            app = EmailInvoiceFinderApp(Mock())
            
            # Mock date entry widgets
            mock_from = Mock()
            mock_from.get.return_value = ""  # Empty
            
            mock_to = Mock()
            mock_to.get.return_value = "2025-12-31"
            mock_to.get_date.return_value = date(2025, 12, 31)
            
            app.date_from_entry = mock_from
            app.date_to_entry = mock_to
            
            is_valid, date_from, date_to, error = app.validate_date_range()
            
            assert is_valid is True
            assert date_from is None
            assert date_to == date(2025, 12, 31)


class TestDateRangeFiltering:
    """Test cases for _email_date_is_within_range method"""
    
    def test_no_range_allows_all(self):
        """Test that with no range (both None), all emails pass"""
        from poczta_faktury import EmailInvoiceFinderApp
        
        with patch('tkinter.Tk'):
            app = EmailInvoiceFinderApp(Mock())
            
            # Test with a date header
            result = app._email_date_is_within_range("Mon, 15 Jun 2025 10:00:00 +0000", None, None)
            assert result is True
    
    def test_email_within_range(self):
        """Test that email within range passes"""
        from poczta_faktury import EmailInvoiceFinderApp
        
        with patch('tkinter.Tk'):
            app = EmailInvoiceFinderApp(Mock())
            
            cutoff_dt = datetime(2025, 6, 1)
            end_dt = datetime(2025, 7, 1)
            
            # Email on 2025-06-15 should be within range
            result = app._email_date_is_within_range("Mon, 15 Jun 2025 10:00:00 +0000", cutoff_dt, end_dt)
            assert result is True
    
    def test_email_before_range(self):
        """Test that email before range is filtered out"""
        from poczta_faktury import EmailInvoiceFinderApp
        
        with patch('tkinter.Tk'):
            app = EmailInvoiceFinderApp(Mock())
            
            cutoff_dt = datetime(2025, 6, 1)
            end_dt = datetime(2025, 7, 1)
            
            # Email on 2025-05-15 should be before range
            result = app._email_date_is_within_range("Mon, 15 May 2025 10:00:00 +0000", cutoff_dt, end_dt)
            assert result is False
    
    def test_email_after_range(self):
        """Test that email after range is filtered out"""
        from poczta_faktury import EmailInvoiceFinderApp
        
        with patch('tkinter.Tk'):
            app = EmailInvoiceFinderApp(Mock())
            
            cutoff_dt = datetime(2025, 6, 1)
            end_dt = datetime(2025, 7, 1)
            
            # Email on 2025-07-15 should be after range
            result = app._email_date_is_within_range("Mon, 15 Jul 2025 10:00:00 +0000", cutoff_dt, end_dt)
            assert result is False
    
    def test_only_start_date(self):
        """Test filtering with only start date (no end)"""
        from poczta_faktury import EmailInvoiceFinderApp
        
        with patch('tkinter.Tk'):
            app = EmailInvoiceFinderApp(Mock())
            
            cutoff_dt = datetime(2025, 6, 1)
            
            # Email after cutoff should pass
            result1 = app._email_date_is_within_range("Mon, 15 Jun 2025 10:00:00 +0000", cutoff_dt, None)
            assert result1 is True
            
            # Email before cutoff should fail
            result2 = app._email_date_is_within_range("Mon, 15 May 2025 10:00:00 +0000", cutoff_dt, None)
            assert result2 is False
    
    def test_only_end_date(self):
        """Test filtering with only end date (no start)"""
        from poczta_faktury import EmailInvoiceFinderApp
        
        with patch('tkinter.Tk'):
            app = EmailInvoiceFinderApp(Mock())
            
            end_dt = datetime(2025, 7, 1)
            
            # Email before end should pass
            result1 = app._email_date_is_within_range("Mon, 15 Jun 2025 10:00:00 +0000", None, end_dt)
            assert result1 is True
            
            # Email after end should fail
            result2 = app._email_date_is_within_range("Mon, 15 Jul 2025 10:00:00 +0000", None, end_dt)
            assert result2 is False
    
    def test_missing_date_header(self):
        """Test that emails without date headers are not filtered out"""
        from poczta_faktury import EmailInvoiceFinderApp
        
        with patch('tkinter.Tk'):
            app = EmailInvoiceFinderApp(Mock())
            
            cutoff_dt = datetime(2025, 6, 1)
            end_dt = datetime(2025, 7, 1)
            
            # Email without date header should pass (don't reject unknown dates)
            result = app._email_date_is_within_range(None, cutoff_dt, end_dt)
            assert result is True
    
    def test_malformed_date_header(self):
        """Test that emails with malformed date headers are not filtered out"""
        from poczta_faktury import EmailInvoiceFinderApp
        
        with patch('tkinter.Tk'):
            app = EmailInvoiceFinderApp(Mock())
            
            cutoff_dt = datetime(2025, 6, 1)
            end_dt = datetime(2025, 7, 1)
            
            # Email with invalid date should pass (don't reject on parse errors)
            result = app._email_date_is_within_range("Invalid Date String", cutoff_dt, end_dt)
            assert result is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
