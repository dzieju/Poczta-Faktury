#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Przykład użycia funkcji wyszukiwania NIP bez GUI
Example of using NIP search functions without GUI
"""

import re


def search_nip_in_text(text, nip):
    """
    Wyszukiwanie numeru NIP w tekście
    Search for NIP number in text
    
    Args:
        text: Tekst do przeszukania / Text to search
        nip: Numer NIP / NIP number
        
    Returns:
        True jeśli NIP znaleziono / True if NIP found
    """
    # Usuń wszystkie znaki niealfanumeryczne z NIP
    clean_nip = re.sub(r'[^0-9]', '', nip)
    
    # Usuń białe znaki z tekstu dla lepszego dopasowania
    clean_text = re.sub(r'\s+', '', text)
    
    # Szukaj NIP jako ciągłej liczby
    if clean_nip in clean_text:
        return True
    
    # Alternatywnie szukaj z możliwymi separatorami (tylko dla NIP o długości 10)
    if len(clean_nip) == 10:
        nip_patterns = [
            '-'.join([clean_nip[:3], clean_nip[3:6], clean_nip[6:8], clean_nip[8:]]),
            '-'.join([clean_nip[:3], clean_nip[3:]]),
        ]
        
        for pattern in nip_patterns:
            if pattern in text:
                return True
    
    return False


def main():
    """Przykłady użycia / Usage examples"""
    
    print("=" * 70)
    print("PRZYKŁADY UŻYCIA APLIKACJI POCZTA FAKTURY")
    print("EXAMPLES OF USING POCZTA FAKTURY APPLICATION")
    print("=" * 70)
    print()
    
    # Przykład 1: Faktura z NIP w formacie z kreskami
    # Example 1: Invoice with NIP in dashed format
    invoice_text_1 = """
    FAKTURA VAT NR 2024/01/001
    
    Sprzedawca:
    Firma ABC Sp. z o.o.
    NIP: 123-456-78-90
    ul. Testowa 1
    00-001 Warszawa
    
    Nabywca:
    Firma XYZ S.A.
    NIP: 987-654-32-10
    
    Kwota netto: 1000,00 PLN
    VAT 23%: 230,00 PLN
    Kwota brutto: 1230,00 PLN
    """
    
    nip_to_find = "1234567890"
    
    if search_nip_in_text(invoice_text_1, nip_to_find):
        print(f"✓ Znaleziono NIP {nip_to_find} w fakturze 1")
    else:
        print(f"✗ Nie znaleziono NIP {nip_to_find} w fakturze 1")
    
    # Przykład 2: Faktura bez kresek w NIP
    # Example 2: Invoice without dashes in NIP
    invoice_text_2 = """
    FAKTURA VAT NR 2024/01/002
    
    Dane sprzedawcy:
    ABC Company
    NIP 9876543210
    
    Wartość: 2500 PLN
    """
    
    nip_to_find_2 = "987-654-32-10"
    
    if search_nip_in_text(invoice_text_2, nip_to_find_2):
        print(f"✓ Znaleziono NIP {nip_to_find_2} w fakturze 2")
    else:
        print(f"✗ Nie znaleziono NIP {nip_to_find_2} w fakturze 2")
    
    # Przykład 3: Faktura z innym NIP
    # Example 3: Invoice with different NIP
    invoice_text_3 = """
    FAKTURA VAT
    NIP: 111-222-33-44
    Kwota: 500 PLN
    """
    
    if search_nip_in_text(invoice_text_3, nip_to_find):
        print(f"✓ Znaleziono NIP {nip_to_find} w fakturze 3")
    else:
        print(f"✗ Nie znaleziono NIP {nip_to_find} w fakturze 3 (prawidłowo)")
    
    print("\n" + "="*70)
    print("NOWE FUNKCJE / NEW FEATURES:")
    print("="*70)
    print()
    print("1. NIEBLOKUJĄCE WYSZUKIWANIE / NON-BLOCKING SEARCH:")
    print("   - GUI pozostaje responsywne podczas wyszukiwania")
    print("   - GUI remains responsive during search")
    print()
    print("2. PRZYCISK PRZERWIJ / STOP BUTTON:")
    print("   - Kliknij 'Przerwij' aby zatrzymać wyszukiwanie")
    print("   - Click 'Przerwij' to stop the search")
    print()
    print("3. USTAWIANIE DATY MODYFIKACJI PLIKÓW / FILE MTIME SETTING:")
    print("   - Zapisane pliki mają datę modyfikacji z nagłówka Date emaila")
    print("   - Saved files have modification time from email Date header")
    print("   - Sprawdź: ls -l --time-style=long-iso <folder>")
    print("   - Check with: ls -l --time-style=long-iso <folder>")
    print()
    print("="*70)
    print("Przykłady zakończone pomyślnie!")
    print("Examples completed successfully!")
    print("="*70)


if __name__ == '__main__':
    main()
