#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration tests for date filtering in email search.

Tests the complete date filtering pipeline including:
- IMAP SEARCH with SINCE operator for server-side filtering
- Client-side date comparison fallback
- UI messages match behavior
"""
import pytest
import unittest.mock as mock
from datetime import datetime, timedelta
import email
from email.utils import formatdate


class TestDateFilterIntegration:
    """Integration tests for date filtering functionality"""
    
    def test_imap_search_filters_server_side_with_cutoff(self):
        """
        Integration test: When cutoff is set, IMAP SEARCH should use SINCE
        to filter on server side, reducing the number of messages fetched.
        """
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
        
        # Mock IMAP connection
        with mock.patch('imaplib.IMAP4_SSL') as mock_imap:
            mock_mail = mock.Mock()
            mock_imap.return_value = mock_mail
            
            # Simulate server-side filtering: SINCE returns fewer messages
            # than ALL would have returned
            mock_mail.search.return_value = ('OK', [b'101 102 103'])  # Only 3 messages after SINCE filter
            mock_mail.select.return_value = ('OK', [])
            
            # Mock stop_event to stop immediately after search
            app.stop_event = mock.Mock()
            app.stop_event.is_set.return_value = True
            
            try:
                # Call the search function
                result = app._search_with_imap_threaded('1234567890', '/tmp', cutoff_dt)
                
                # Verify that search was called once with SINCE criteria
                assert mock_mail.search.call_count == 1, \
                    f"Expected 1 search call, got {mock_mail.search.call_count}"
                
                # Verify SINCE was used
                search_args = mock_mail.search.call_args[0]
                search_criteria = search_args[1] if len(search_args) > 1 else None
                assert 'SINCE' in search_criteria, \
                    f"Expected SINCE in search criteria, got: {search_criteria}"
                
                # Verify we only got messages from server that match the filter
                # (not fetching all 80398 messages as mentioned in the problem statement)
                assert result == 0, "No invoices should be found in this mock test"
                
            finally:
                root.destroy()
    
    def test_client_side_filtering_consistency(self):
        """
        Integration test: Verify that client-side filtering keeps messages
        newer than (>=) cutoff, not older than (<=) cutoff.
        """
        import tkinter as tk
        from poczta_faktury import EmailInvoiceFinderApp
        
        # Create app instance
        root = tk.Tk()
        app = EmailInvoiceFinderApp(root)
        
        try:
            # Set cutoff to December 1, 2025
            cutoff_dt = datetime(2025, 12, 1, 0, 0, 0)
            
            # Create test email dates
            dates_to_test = [
                # (date_string, should_pass, description)
                ("Mon, 15 Dec 2025 10:00:00 +0000", True, "15 days after cutoff"),
                ("Sun, 01 Dec 2025 00:00:00 +0000", True, "exactly at cutoff"),
                ("Sun, 01 Dec 2025 12:00:00 +0000", True, "same day as cutoff, later time"),
                ("Sat, 30 Nov 2025 23:59:59 +0000", False, "1 second before cutoff"),
                ("Sat, 15 Nov 2025 10:00:00 +0000", False, "15 days before cutoff"),
                ("Mon, 01 Nov 2025 10:00:00 +0000", False, "30 days before cutoff"),
            ]
            
            for date_str, should_pass, description in dates_to_test:
                result = app._email_date_is_within_cutoff(date_str, cutoff_dt)
                
                if should_pass:
                    assert result is True, \
                        f"Failed for {description}: {date_str} should be KEPT (newer than cutoff {cutoff_dt})"
                else:
                    assert result is False, \
                        f"Failed for {description}: {date_str} should be FILTERED OUT (older than cutoff {cutoff_dt})"
            
        finally:
            root.destroy()
    
    def test_server_side_and_client_side_filters_work_together(self):
        """
        Integration test: Verify that server-side SINCE and client-side
        filtering work together correctly.
        
        Server-side SINCE should filter most messages, and client-side should
        provide additional filtering for edge cases or if needed.
        """
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
        
        # Set up cutoff date (7 days ago)
        cutoff_dt = datetime.now() - timedelta(days=7)
        cutoff_date_str = cutoff_dt.strftime("%d-%b-%Y")
        
        # Mock IMAP connection
        with mock.patch('imaplib.IMAP4_SSL') as mock_imap:
            mock_mail = mock.Mock()
            mock_imap.return_value = mock_mail
            
            # Server returns messages after filtering with SINCE
            # These are message IDs that passed server-side filter
            mock_mail.search.return_value = ('OK', [b'101 102 103'])
            mock_mail.select.return_value = ('OK', [])
            
            # Mock fetch to return emails with various dates
            # Some within cutoff (should be processed) and some edge cases
            def mock_fetch(msg_id, fetch_spec):
                msg_num = int(msg_id)
                
                # Create a mock email message
                msg = email.message.Message()
                
                if msg_num == 101:
                    # 5 days ago (within cutoff) - use standard date format
                    msg['Date'] = 'Mon, 10 Dec 2025 10:00:00 +0000'
                elif msg_num == 102:
                    # Today (within cutoff)
                    msg['Date'] = 'Sun, 15 Dec 2025 10:00:00 +0000'
                elif msg_num == 103:
                    # Well within cutoff (should be included)
                    msg['Date'] = 'Wed, 11 Dec 2025 10:00:00 +0000'
                
                msg['Subject'] = f'Test message {msg_num}'
                
                return ('OK', [(msg_id, msg.as_bytes())])
            
            mock_mail.fetch.side_effect = mock_fetch
            
            # Mock stop_event to process all messages
            app.stop_event = mock.Mock()
            app.stop_event.is_set.return_value = False
            
            # Track which messages were processed
            processed_messages = []
            original_decode = app.decode_email_subject
            def track_decode(subject):
                processed_messages.append(subject)
                return original_decode(subject)
            
            app.decode_email_subject = track_decode
            
            try:
                # Call the search function
                result = app._search_with_imap_threaded('1234567890', '/tmp', cutoff_dt)
                
                # Verify server-side SINCE was used
                search_calls = mock_mail.search.call_args_list
                assert len(search_calls) == 1
                search_criteria = search_calls[0][0][1]
                assert 'SINCE' in search_criteria
                assert cutoff_date_str in search_criteria
                
                # Verify all messages from server were processed
                # (they all passed both server-side SINCE and client-side filtering)
                assert mock_mail.fetch.call_count == 3, \
                    f"Expected 3 fetches (one per message), got {mock_mail.fetch.call_count}"
                
                # All messages should have been processed because they all
                # meet the date criteria (>= cutoff)
                assert len(processed_messages) == 3, \
                    f"Expected 3 messages processed, got {len(processed_messages)}"
                
            finally:
                root.destroy()
    
    def test_no_cutoff_searches_all_messages(self):
        """
        Integration test: When no cutoff is set, search should use 'ALL'
        and process all messages without date filtering.
        """
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
            
            # Server returns all messages (no date filtering)
            mock_mail.search.return_value = ('OK', [b'1 2 3 4 5'])
            mock_mail.select.return_value = ('OK', [])
            
            # Mock stop_event to stop immediately
            app.stop_event = mock.Mock()
            app.stop_event.is_set.return_value = True
            
            try:
                # Call the search function
                result = app._search_with_imap_threaded('1234567890', '/tmp', cutoff_dt)
                
                # Verify that search was called with 'ALL' (no date filter)
                search_calls = mock_mail.search.call_args_list
                assert len(search_calls) == 1
                search_criteria = search_calls[0][0][1]
                assert search_criteria == 'ALL', \
                    f"Expected 'ALL' when no cutoff, got: {search_criteria}"
                
            finally:
                root.destroy()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
