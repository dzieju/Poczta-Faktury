#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for IMAP date range helper functions.

Tests the imap_date and imap_date_range_last_n_days functions to ensure
correct date formatting and range calculation for IMAP SEARCH commands.
"""
import pytest
import datetime
from poczta_faktury.imap_date_range import imap_date, imap_date_range_last_n_days


class TestImapDate:
    """Test cases for imap_date function"""
    
    def test_basic_date_format(self):
        """Test basic date formatting to DD-MMM-YYYY"""
        date = datetime.date(2025, 12, 15)
        result = imap_date(date)
        assert result == "15-Dec-2025"
    
    def test_january_date(self):
        """Test date formatting for January"""
        date = datetime.date(2025, 1, 1)
        result = imap_date(date)
        assert result == "01-Jan-2025"
    
    def test_december_date(self):
        """Test date formatting for December"""
        date = datetime.date(2025, 12, 31)
        result = imap_date(date)
        assert result == "31-Dec-2025"
    
    def test_single_digit_day(self):
        """Test that single digit days are zero-padded"""
        date = datetime.date(2025, 6, 5)
        result = imap_date(date)
        assert result == "05-Jun-2025"


class TestImapDateRangeLastNDays:
    """Test cases for imap_date_range_last_n_days function"""
    
    def test_single_day(self):
        """Test n_days=1 returns today only"""
        today = datetime.date(2025, 12, 15)
        start, before = imap_date_range_last_n_days(1, today=today)
        
        # Start should be today
        assert start == "15-Dec-2025"
        # Before should be tomorrow (exclusive)
        assert before == "16-Dec-2025"
    
    def test_seven_days(self):
        """Test n_days=7 returns last week including today"""
        today = datetime.date(2025, 12, 15)
        start, before = imap_date_range_last_n_days(7, today=today)
        
        # Start should be 6 days ago (15 - 6 = 9)
        assert start == "09-Dec-2025"
        # Before should be tomorrow
        assert before == "16-Dec-2025"
    
    def test_thirty_days(self):
        """Test n_days=30 returns last 30 days"""
        today = datetime.date(2025, 12, 15)
        start, before = imap_date_range_last_n_days(30, today=today)
        
        # Start should be 29 days ago (15 - 29 = -14, wraps to Nov 16)
        assert start == "16-Nov-2025"
        # Before should be tomorrow
        assert before == "16-Dec-2025"
    
    def test_invalid_n_days_zero(self):
        """Test that n_days=0 raises ValueError"""
        today = datetime.date(2025, 12, 15)
        
        with pytest.raises(ValueError) as exc_info:
            imap_date_range_last_n_days(0, today=today)
        
        assert "must be >= 1" in str(exc_info.value)
    
    def test_invalid_n_days_negative(self):
        """Test that negative n_days raises ValueError"""
        today = datetime.date(2025, 12, 15)
        
        with pytest.raises(ValueError) as exc_info:
            imap_date_range_last_n_days(-5, today=today)
        
        assert "must be >= 1" in str(exc_info.value)
    
    def test_year_boundary_forward(self):
        """Test date range crossing year boundary (Dec to Jan)"""
        # Testing with Dec 29, going back 7 days should stay in December
        today = datetime.date(2025, 12, 29)
        start, before = imap_date_range_last_n_days(7, today=today)
        
        assert start == "23-Dec-2025"
        assert before == "30-Dec-2025"
    
    def test_year_boundary_backward(self):
        """Test date range crossing year boundary backward (Jan to Dec)"""
        # Testing with Jan 3, going back 7 days should cross into previous year
        today = datetime.date(2025, 1, 3)
        start, before = imap_date_range_last_n_days(7, today=today)
        
        # Start should be Dec 28, 2024 (3 - 6 = -3, wraps to prev year)
        assert start == "28-Dec-2024"
        # Before should be Jan 4, 2025
        assert before == "04-Jan-2025"
    
    def test_month_abbreviations(self):
        """Test that all month abbreviations are correctly formatted"""
        months = [
            (datetime.date(2025, 1, 15), "Jan"),
            (datetime.date(2025, 2, 15), "Feb"),
            (datetime.date(2025, 3, 15), "Mar"),
            (datetime.date(2025, 4, 15), "Apr"),
            (datetime.date(2025, 5, 15), "May"),
            (datetime.date(2025, 6, 15), "Jun"),
            (datetime.date(2025, 7, 15), "Jul"),
            (datetime.date(2025, 8, 15), "Aug"),
            (datetime.date(2025, 9, 15), "Sep"),
            (datetime.date(2025, 10, 15), "Oct"),
            (datetime.date(2025, 11, 15), "Nov"),
            (datetime.date(2025, 12, 15), "Dec"),
        ]
        
        for test_date, expected_month in months:
            start, before = imap_date_range_last_n_days(1, today=test_date)
            assert expected_month in start
    
    def test_default_today_parameter(self):
        """Test that today parameter defaults to current date"""
        # This test just verifies the function works without today parameter
        start, before = imap_date_range_last_n_days(1)
        
        # Should return valid IMAP format dates
        assert len(start.split('-')) == 3
        assert len(before.split('-')) == 3
        
        # Verify format matches DD-MMM-YYYY pattern
        import re
        pattern = r'^\d{2}-[A-Z][a-z]{2}-\d{4}$'
        assert re.match(pattern, start)
        assert re.match(pattern, before)
    
    def test_leap_year_february(self):
        """Test date range in leap year February"""
        # 2024 is a leap year
        today = datetime.date(2024, 2, 29)
        start, before = imap_date_range_last_n_days(1, today=today)
        
        assert start == "29-Feb-2024"
        assert before == "01-Mar-2024"
    
    def test_range_spans_exactly_n_days(self):
        """Verify that the range spans exactly N days"""
        today = datetime.date(2025, 12, 15)
        
        # For 7 days: Dec 9, 10, 11, 12, 13, 14, 15 = 7 days
        start, before = imap_date_range_last_n_days(7, today=today)
        
        start_date = datetime.datetime.strptime(start, "%d-%b-%Y").date()
        before_date = datetime.datetime.strptime(before, "%d-%b-%Y").date()
        
        # before_date - start_date should equal n_days
        days_diff = (before_date - start_date).days
        assert days_diff == 7
        
        # Also verify start is 6 days before today
        assert (today - start_date).days == 6
        
        # And before is 1 day after today
        assert (before_date - today).days == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
