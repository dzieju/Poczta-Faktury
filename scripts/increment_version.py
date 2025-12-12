#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt do automatycznego zwiększania wersji aplikacji (patch).
Zwiększa ostatnią cyfrę w wersji semver (major.minor.patch).
"""

import sys
import re
from pathlib import Path


def increment_version(version_file_path):
    """
    Zwiększa wersję patch w pliku version.txt
    
    Args:
        version_file_path: Ścieżka do pliku version.txt
        
    Returns:
        Nowa wersja jako string
    """
    version_path = Path(version_file_path)
    
    # Odczytaj aktualną wersję
    if version_path.exists():
        try:
            current_version = version_path.read_text().strip()
        except Exception:
            current_version = "1.0.0"
    else:
        current_version = "1.0.0"
    
    # Parsuj wersję (format: major.minor.patch)
    version_pattern = r'^(\d+)\.(\d+)\.(\d+)$'
    match = re.match(version_pattern, current_version)
    
    if match:
        major = int(match.group(1))
        minor = int(match.group(2))
        patch = int(match.group(3))
        
        # Zwiększ patch
        patch += 1
        new_version = f"{major}.{minor}.{patch}"
    else:
        # Nieprawidłowy format - resetuj do 1.0.0
        new_version = "1.0.0"
    
    # Zapisz nową wersję
    version_path.write_text(new_version)
    
    return new_version


def main():
    if len(sys.argv) < 2:
        print("Użycie: python increment_version.py <ścieżka_do_version.txt>")
        sys.exit(1)
    
    version_file = sys.argv[1]
    
    try:
        new_version = increment_version(version_file)
        print(new_version)
    except Exception as e:
        print(f"Błąd: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
