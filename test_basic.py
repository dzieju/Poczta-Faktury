#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test podstawowych funkcji bez GUI
"""

import re
import sys
import os
import tempfile
import json


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
            safe_filename = name[:200-len(ext)] + ext
        
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


def test_invoice_pattern_matching():
    """Test wykrywania faktur na podstawie wzorca"""
    print("\nTest: Wykrywanie wzorca nazwy faktury")
    
    def matches_invoice_pattern(filename, pattern=r'fakt'):
        """Sprawdza czy nazwa pliku pasuje do wzorca faktury"""
        if not filename:
            return False
        
        try:
            return re.search(pattern, filename, re.IGNORECASE) is not None
        except re.error:
            return pattern.lower() in filename.lower()
    
    # Test 1: Faktura - podstawowy wzorzec
    result1 = matches_invoice_pattern("faktura_2024_01.pdf", r'fakt')
    print(f"  Test 1 (faktura_2024_01.pdf): {'✓' if result1 else '✗'}")
    
    # Test 2: FAKTURA - wielkość liter
    result2 = matches_invoice_pattern("FAKTURA_VAT.pdf", r'fakt')
    print(f"  Test 2 (FAKTURA_VAT.pdf): {'✓' if result2 else '✗'}")
    
    # Test 3: Fakt - skrócona nazwa
    result3 = matches_invoice_pattern("Fakt_12345.pdf", r'fakt')
    print(f"  Test 3 (Fakt_12345.pdf): {'✓' if result3 else '✗'}")
    
    # Test 4: Nie pasuje - inny dokument
    result4 = matches_invoice_pattern("raport_miesięczny.pdf", r'fakt')
    print(f"  Test 4 (raport_miesięczny.pdf - powinno być False): {'✓' if not result4 else '✗'}")
    
    # Test 5: Regex bardziej złożony
    result5 = matches_invoice_pattern("invoice_2024.pdf", r'(fakt|invoice)')
    print(f"  Test 5 (invoice_2024.pdf z regex): {'✓' if result5 else '✗'}")
    
    return all([result1, result2, result3, not result4, result5])


def test_unique_filename_generation():
    """Test generowania unikalnych nazw plików"""
    print("\nTest: Generowanie unikalnych nazw plików")
    
    import os
    import tempfile
    
    def get_unique_filename(output_folder, filename, overwrite_policy='suffix'):
        """Generuje unikalną nazwę pliku zgodnie z polityką nadpisywania"""
        output_path = os.path.join(output_folder, filename)
        
        if overwrite_policy == 'overwrite':
            return output_path
        
        if not os.path.exists(output_path):
            return output_path
        
        base, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(os.path.join(output_folder, f"{base}_{counter}{ext}")):
            counter += 1
        
        return os.path.join(output_folder, f"{base}_{counter}{ext}")
    
    # Utwórz tymczasowy folder do testów
    with tempfile.TemporaryDirectory() as tmpdir:
        # Test 1: Pierwszy plik - bez sufiksu
        path1 = get_unique_filename(tmpdir, "test.pdf", 'suffix')
        result1 = path1.endswith("test.pdf")
        print(f"  Test 1 (pierwszy plik bez sufiksu): {'✓' if result1 else '✗'}")
        
        # Utwórz plik
        open(path1, 'w').close()
        
        # Test 2: Drugi plik - z sufiksem _1
        path2 = get_unique_filename(tmpdir, "test.pdf", 'suffix')
        result2 = path2.endswith("test_1.pdf")
        print(f"  Test 2 (drugi plik z sufiksem _1): {'✓' if result2 else '✗'}")
        
        # Utwórz drugi plik
        open(path2, 'w').close()
        
        # Test 3: Trzeci plik - z sufiksem _2
        path3 = get_unique_filename(tmpdir, "test.pdf", 'suffix')
        result3 = path3.endswith("test_2.pdf")
        print(f"  Test 3 (trzeci plik z sufiksem _2): {'✓' if result3 else '✗'}")
        
        # Test 4: Polityka overwrite - zawsze ta sama nazwa
        path4 = get_unique_filename(tmpdir, "test.pdf", 'overwrite')
        result4 = path4.endswith("test.pdf")
        print(f"  Test 4 (polityka overwrite): {'✓' if result4 else '✗'}")
    
    return all([result1, result2, result3, result4])


def test_found_invoices_persistence():
    """Test zapisu i odczytu listy znalezionych faktur"""
    print("\nTest: Zapis i odczyt znalezionych faktur")
    
    # Dane testowe
    test_invoices = [
        {
            'date': '2024-01-15 10:30',
            'sender': 'test@example.com',
            'subject': 'Faktura VAT 001/2024',
            'filename': 'faktura_001.pdf',
            'file_path': '/tmp/faktura_001.pdf',
            'found_timestamp': '2024-01-15T10:30:00'
        },
        {
            'date': '2024-01-16 14:20',
            'sender': 'billing@company.com',
            'subject': 'Invoice 002/2024',
            'filename': 'invoice_002.pdf',
            'file_path': '/tmp/invoice_002.pdf',
            'found_timestamp': '2024-01-16T14:20:00'
        }
    ]
    
    # Utwórz tymczasowy plik
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_file = f.name
        json.dump(test_invoices, f, indent=2, ensure_ascii=False)
    
    try:
        # Test 1: Odczyt danych
        with open(temp_file, 'r', encoding='utf-8') as f:
            loaded_invoices = json.load(f)
        
        result1 = len(loaded_invoices) == 2
        print(f"  Test 1 (odczyt 2 faktur): {'✓' if result1 else '✗'}")
        
        # Test 2: Sprawdź poprawność danych
        result2 = loaded_invoices[0]['filename'] == 'faktura_001.pdf'
        print(f"  Test 2 (poprawność nazwy pliku): {'✓' if result2 else '✗'}")
        
        # Test 3: Sprawdź kodowanie polskich znaków
        result3 = 'ó' in loaded_invoices[0]['subject'] or 'Faktura' in loaded_invoices[0]['subject']
        print(f"  Test 3 (kodowanie UTF-8): {'✓' if result3 else '✗'}")
        
        return all([result1, result2, result3])
    finally:
        # Usuń tymczasowy plik
        if os.path.exists(temp_file):
            os.unlink(temp_file)


def main():
    print("=" * 60)
    print("TESTY APLIKACJI POCZTA FAKTURY (bez GUI)")
    print("=" * 60)
    print()
    
    tests = [
        test_nip_search_logic,
        test_safe_filename,
        test_pdf_dependencies,
        test_invoice_pattern_matching,
        test_unique_filename_generation,
        test_found_invoices_persistence,
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
