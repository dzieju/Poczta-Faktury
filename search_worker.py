#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Search worker module - provides search functionality with queue-based result streaming
This module is designed to work with the existing EmailInvoiceFinderApp implementation.
"""
from threading import Event


class SearchStop(Event):
    """Event class for signaling search stop"""
    pass
