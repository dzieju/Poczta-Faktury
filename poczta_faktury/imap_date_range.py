#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IMAP date range helper functions for email search.

This module provides utilities for converting dates to IMAP format and calculating
date ranges for IMAP SEARCH commands. IMAP compares dates only (not times), and
the BEFORE criterion is exclusive (messages before but not on that date).

Example usage:
    >>> from datetime import date
    >>> from poczta_faktury.imap_date_range import imap_date, imap_date_range_last_n_days
    >>> 
    >>> # Format a single date
    >>> imap_date(date(2025, 12, 15))
    '15-Dec-2025'
    >>> 
    >>> # Get date range for last 7 days
    >>> start, before = imap_date_range_last_n_days(7, today=date(2025, 12, 15))
    >>> print(f"SINCE {start} BEFORE {before}")
    SINCE 09-Dec-2025 BEFORE 16-Dec-2025
    >>> 
    >>> # This searches messages from 09-Dec-2025 through 15-Dec-2025 (inclusive)
"""

import datetime
from typing import Optional, Tuple


def imap_date(date: datetime.date) -> str:
    """
    Convert a date to IMAP format (DD-MMM-YYYY).
    
    Args:
        date: The date to format
        
    Returns:
        Date string in IMAP format, e.g., "15-Dec-2025"
        
    Example:
        >>> imap_date(datetime.date(2025, 12, 15))
        '15-Dec-2025'
    """
    return date.strftime("%d-%b-%Y")


def imap_date_range_last_n_days(
    n_days: int, 
    today: Optional[datetime.date] = None
) -> Tuple[str, str]:
    """
    Calculate IMAP date range for the last N days including today.
    
    Returns a tuple (since_date, before_date) suitable for IMAP SEARCH:
    - since_date: The start date (today - n_days + 1), inclusive
    - before_date: The end date (today + 1), exclusive
    
    This ensures exactly N days are searched, with today being the last day.
    
    Args:
        n_days: Number of days to include (must be >= 1)
        today: The reference date (defaults to today in UTC if not provided)
        
    Returns:
        Tuple of (since_date, before_date) in IMAP format
        
    Raises:
        ValueError: If n_days < 1
        
    Example:
        >>> # Search last 7 days including today (2025-12-15)
        >>> start, before = imap_date_range_last_n_days(7, datetime.date(2025, 12, 15))
        >>> start
        '09-Dec-2025'
        >>> before
        '16-Dec-2025'
        >>> # IMAP will search: 09-Dec-2025 <= date < 16-Dec-2025
        >>> # Which includes: 09, 10, 11, 12, 13, 14, 15 Dec (7 days)
        
        >>> # Search only today
        >>> start, before = imap_date_range_last_n_days(1, datetime.date(2025, 12, 15))
        >>> start
        '15-Dec-2025'
        >>> before
        '16-Dec-2025'
    """
    if n_days < 1:
        raise ValueError(f"n_days must be >= 1, got {n_days}")
    
    if today is None:
        today = datetime.datetime.now(datetime.UTC).date()
    
    # Calculate start date: today - (n_days - 1)
    # For n_days=7, we want today and the previous 6 days
    start_date = today - datetime.timedelta(days=n_days - 1)
    
    # Calculate before date: today + 1 (BEFORE is exclusive)
    before_date = today + datetime.timedelta(days=1)
    
    return (imap_date(start_date), imap_date(before_date))


if __name__ == '__main__':
    import sys
    
    # CLI demo
    if len(sys.argv) > 1:
        try:
            n = int(sys.argv[1])
            today = datetime.datetime.now(datetime.UTC).date()
            start, before = imap_date_range_last_n_days(n, today)
            
            print(f"Searching last {n} days (including today: {imap_date(today)})")
            print(f"IMAP criteria: SINCE {start} BEFORE {before}")
            print(f"\nThis will search messages from {start} through {imap_date(today)} (inclusive)")
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Usage: python -m poczta_faktury.imap_date_range <n_days>")
        print("Example: python -m poczta_faktury.imap_date_range 7")
        sys.exit(1)
