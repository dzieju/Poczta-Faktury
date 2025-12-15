#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for IMAP SINCE date filtering functionality.

Tests that the IMAP search correctly uses server-side SINCE operator
when a cutoff date is provided, and uses ALL when no cutoff is provided.
"""
import pytest
import unittest.mock as mock
from datetime import datetime, timedelta
import imaplib


class TestImapSinceFilter:
    """Test cases for IMAP SINCE date filtering"""
    
    def test_imap_search_with_cutoff_uses_since(self):
        """Test that IMAP search uses SINCE operator when cutoff_dt is provided"""
        # Import the app class
        import tkinter as tk
        from poczta_faktury import EmailInvoiceFinderApp
        
        # Create app instance
        root = tk.Tk()
        app = EmailInvoiceFinderApp(root)
        
        # Set up mock email config
        app.email_config = {
            'server': 'imap.test.com',
            'port': 993,
            'email': 'test@test.com',
            'password': 'testpass',
            'use_ssl': True
        }
        
        # Set up cutoff date (30 days ago)
        cutoff_dt = datetime.now() - timedelta(days=30)
        expected_since_date = cutoff_dt.strftime("%d-%b-%Y")
        
        # Mock IMAP connection
        with mock.patch('imaplib.IMAP4_SSL') as mock_imap:
            mock_mail = mock.Mock()
            mock_imap.return_value = mock_mail
            
            # Mock the search to return empty results
            mock_mail.search.return_value = ('OK', [b''])
            mock_mail.select.return_value = ('OK', [])
            
            # Mock stop_event to stop immediately
            app.stop_event = mock.Mock()
            app.stop_event.is_set.return_value = True
            
            try:
                # Call the search function
                app._search_with_imap_threaded('1234567890', '/tmp', cutoff_dt)
                
                # Verify that search was called with SINCE criteria
                search_calls = mock_mail.search.call_args_list
                assert len(search_calls) > 0, "IMAP search was not called"
                
                # Get the search criteria from the call
                search_args = search_calls[0][0]
                search_criteria = search_args[1] if len(search_args) > 1 else None
                
                # Verify SINCE is in the search criteria
                assert search_criteria is not None, "Search criteria is None"
                assert 'SINCE' in search_criteria, f"SINCE not found in search criteria: {search_criteria}"
                assert expected_since_date in search_criteria, \
                    f"Expected date {expected_since_date} not found in search criteria: {search_criteria}"
                
            finally:
                root.destroy()
    
    def test_imap_search_without_cutoff_uses_all(self):
        """Test that IMAP search uses ALL when no cutoff_dt is provided"""
        # Import the app class
        import tkinter as tk
        from poczta_faktury import EmailInvoiceFinderApp
        
        # Create app instance
        root = tk.Tk()
        app = EmailInvoiceFinderApp(root)
        
        # Set up mock email config
        app.email_config = {
            'server': 'imap.test.com',
            'port': 993,
            'email': 'test@test.com',
            'password': 'testpass',
            'use_ssl': True
        }
        
        # No cutoff date
        cutoff_dt = None
        
        # Mock IMAP connection
        with mock.patch('imaplib.IMAP4_SSL') as mock_imap:
            mock_mail = mock.Mock()
            mock_imap.return_value = mock_mail
            
            # Mock the search to return empty results
            mock_mail.search.return_value = ('OK', [b''])
            mock_mail.select.return_value = ('OK', [])
            
            # Mock stop_event to stop immediately
            app.stop_event = mock.Mock()
            app.stop_event.is_set.return_value = True
            
            try:
                # Call the search function
                app._search_with_imap_threaded('1234567890', '/tmp', cutoff_dt)
                
                # Verify that search was called with ALL criteria
                search_calls = mock_mail.search.call_args_list
                assert len(search_calls) > 0, "IMAP search was not called"
                
                # Get the search criteria from the call
                search_args = search_calls[0][0]
                search_criteria = search_args[1] if len(search_args) > 1 else None
                
                # Verify ALL is used
                assert search_criteria == 'ALL', \
                    f"Expected 'ALL' but got: {search_criteria}"
                
            finally:
                root.destroy()
    
    def test_imap_since_date_format(self):
        """Test that the SINCE date is formatted correctly for IMAP (DD-MMM-YYYY)"""
        # Import the app class
        import tkinter as tk
        from poczta_faktury import EmailInvoiceFinderApp
        
        # Create app instance
        root = tk.Tk()
        app = EmailInvoiceFinderApp(root)
        
        # Set up mock email config
        app.email_config = {
            'server': 'imap.test.com',
            'port': 993,
            'email': 'test@test.com',
            'password': 'testpass',
            'use_ssl': True
        }
        
        # Set up specific cutoff date for testing
        cutoff_dt = datetime(2025, 12, 15)
        
        # Mock IMAP connection
        with mock.patch('imaplib.IMAP4_SSL') as mock_imap:
            mock_mail = mock.Mock()
            mock_imap.return_value = mock_mail
            
            # Mock the search to return empty results
            mock_mail.search.return_value = ('OK', [b''])
            mock_mail.select.return_value = ('OK', [])
            
            # Mock stop_event to stop immediately
            app.stop_event = mock.Mock()
            app.stop_event.is_set.return_value = True
            
            try:
                # Call the search function
                app._search_with_imap_threaded('1234567890', '/tmp', cutoff_dt)
                
                # Verify that search was called with correctly formatted date
                search_calls = mock_mail.search.call_args_list
                assert len(search_calls) > 0, "IMAP search was not called"
                
                # Get the search criteria from the call
                search_args = search_calls[0][0]
                search_criteria = search_args[1] if len(search_args) > 1 else None
                
                # Verify date format (DD-MMM-YYYY)
                assert '15-Dec-2025' in search_criteria, \
                    f"Expected '15-Dec-2025' in search criteria: {search_criteria}"
                
            finally:
                root.destroy()
    
    def test_client_side_filtering_keeps_newer_messages(self):
        """Test that client-side filtering keeps messages NEWER than cutoff (not older)"""
        # Import the app class
        import tkinter as tk
        from poczta_faktury import EmailInvoiceFinderApp
        
        # Create app instance
        root = tk.Tk()
        app = EmailInvoiceFinderApp(root)
        
        try:
            # Test with messages newer than cutoff (should be kept)
            cutoff_dt = datetime(2025, 12, 1)
            newer_date_header = "Mon, 15 Dec 2025 10:00:00 +0000"
            
            result = app._email_date_is_within_cutoff(newer_date_header, cutoff_dt)
            assert result is True, \
                f"Message newer than cutoff should be kept (cutoff: {cutoff_dt}, message: {newer_date_header})"
            
            # Test with messages older than cutoff (should be filtered out)
            older_date_header = "Mon, 15 Nov 2025 10:00:00 +0000"
            
            result = app._email_date_is_within_cutoff(older_date_header, cutoff_dt)
            assert result is False, \
                f"Message older than cutoff should be filtered out (cutoff: {cutoff_dt}, message: {older_date_header})"
            
            # Test with message exactly at cutoff (should be kept - inclusive)
            exact_date_header = "Sun, 01 Dec 2025 00:00:00 +0000"
            
            result = app._email_date_is_within_cutoff(exact_date_header, cutoff_dt)
            assert result is True, \
                f"Message at exact cutoff should be kept (cutoff: {cutoff_dt}, message: {exact_date_header})"
            
        finally:
            root.destroy()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
