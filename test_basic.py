#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test podstawowych funkcji bez GUI
"""

import re
import sys


def test_nip_search_logic():
    """Test logiki wyszukiwania NIP"""
    print("Test: Logika wyszukiwania NIP")
    
    def search_nip_in_text(text, nip):
        """Wyszukiwanie numeru NIP w tekście"""
        # Usuń wszystkie znaki niealfanumeryczne z NIP
        clean_nip = re.sub(r'[^0-9]', '', nip)
        
        # Usuń białe znaki z tekstu dla lepszego dopasowania
        clean_text = re.sub(r'\s+', '', text)
        
        # Szukaj NIP jako ciągłej liczby
        if clean_nip in clean_text:
            return True
        
        # Alternatywnie szukaj z możliwymi separatorami
        nip_patterns = [
            clean_nip,
            '-'.join([clean_nip[:3], clean_nip[3:6], clean_nip[6:8], clean_nip[8:]]),
            '-'.join([clean_nip[:3], clean_nip[3:]]),
        ]
        
        for pattern in nip_patterns:
            if pattern in text:
                return True
        
        return False
    
    # Test 1: NIP z kreskami
    test_text1 = "Faktura VAT\nNIP: 123-456-78-90\nKwota: 1000 PLN"
    nip1 = "1234567890"
    result1 = search_nip_in_text(test_text1, nip1)
    print(f"  Test 1 (NIP z kreskami): {'✓' if result1 else '✗'}")
    
    # Test 2: NIP bez separatorów
    test_text2 = "Faktura VAT\nNIP 1234567890\nKwota: 1000 PLN"
    result2 = search_nip_in_text(test_text2, nip1)
    print(f"  Test 2 (NIP bez separatorów): {'✓' if result2 else '✗'}")
    
    # Test 3: NIP w ciągłym tekście
    test_text3 = "FakturaVATNIP1234567890Kwota1000PLN"
    result3 = search_nip_in_text(test_text3, nip1)
    print(f"  Test 3 (NIP w ciągłym tekście): {'✓' if result3 else '✗'}")
    
    # Test 4: Brak NIP
    test_text4 = "Faktura VAT\nNIP: 999-888-77-66\nKwota: 1000 PLN"
    result4 = search_nip_in_text(test_text4, nip1)
    print(f"  Test 4 (Brak NIP - powinno być False): {'✓' if not result4 else '✗'}")
    
    return all([result1, result2, result3, not result4])


def test_safe_filename():
    """Test bezpiecznych nazw plików"""
    print("\nTest: Bezpieczne nazwy plików")
    
    import os
    
    def make_safe_filename(filename):
        """Tworzenie bezpiecznej nazwy pliku"""
        # Weź tylko nazwę pliku (bez ścieżki)
        filename = os.path.basename(filename)
        
        # Usuń niebezpieczne znaki
        safe_chars = '-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789ąćęłńóśźżĄĆĘŁŃÓŚŹŻ'
        safe_filename = ''.join(c for c in filename if c in safe_chars)
        
        # Ogranicz długość
        if len(safe_filename) > 200:
            name, ext = os.path.splitext(safe_filename)
            safe_filename = name[:196] + ext
        
        return safe_filename if safe_filename else 'faktura.pdf'
    
    # Test 1: Niebezpieczna ścieżka
    unsafe1 = "faktura/../../../etc/passwd.pdf"
    safe1 = make_safe_filename(unsafe1)
    result1 = '/' not in safe1 and '..' not in safe1
    print(f"  Test 1 (Usunięcie ../): {'✓' if result1 else '✗'} ({safe1})")
    
    # Test 2: Znaki specjalne
    unsafe2 = "faktura<>:\"|?*.pdf"
    safe2 = make_safe_filename(unsafe2)
    result2 = all(c not in safe2 for c in '<>:"|?*')
    print(f"  Test 2 (Znaki specjalne): {'✓' if result2 else '✗'} ({safe2})")
    
    # Test 3: Prawidłowa nazwa
    safe_input = "faktura_2024_01.pdf"
    safe3 = make_safe_filename(safe_input)
    result3 = safe3 == safe_input
    print(f"  Test 3 (Prawidłowa nazwa): {'✓' if result3 else '✗'} ({safe3})")
    
    return all([result1, result2, result3])


def test_pdf_dependencies():
    """Test dostępności bibliotek PDF"""
    print("\nTest: Biblioteki PDF")
    
    try:
        import PyPDF2
        print("  ✓ PyPDF2 zainstalowany")
        has_pypdf2 = True
    except ImportError:
        print("  ✗ PyPDF2 nie zainstalowany")
        has_pypdf2 = False
    
    try:
        import pdfplumber
        print("  ✓ pdfplumber zainstalowany")
        has_pdfplumber = True
    except ImportError:
        print("  ✗ pdfplumber nie zainstalowany")
        has_pdfplumber = False
    
    return has_pypdf2 and has_pdfplumber


def main():
    print("=" * 60)
    print("TESTY APLIKACJI POCZTA FAKTURY (bez GUI)")
    print("=" * 60)
    print()
    
    tests = [
        test_nip_search_logic,
        test_safe_filename,
        test_pdf_dependencies,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  ✗ Nieoczekiwany błąd: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    passed = sum(results)
    total = len(results)
    
    print()
    print("=" * 60)
    print(f"WYNIKI: {passed}/{total} testów zaliczonych")
    print("=" * 60)
    
    return all(results)


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
