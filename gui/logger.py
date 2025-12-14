"""
Simple logging module for GUI components
"""
import sys
from datetime import datetime


def log(message, level="INFO"):
    """
    Simple logging function that prints to stdout with timestamp
    
    Args:
        message: Message to log
        level: Log level (INFO, WARNING, ERROR, DEBUG)
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}", flush=True)
    sys.stdout.flush()
