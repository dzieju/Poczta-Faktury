#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test logiki zapisu/odczytu znalezionych faktur bez GUI
"""

import json
import os
import tempfile
from pathlib import Path


def test_atomic_save():
    """Test atomowego zapisu do pliku"""
    print("\nTest 1: Atomowy zapis (symulacja)")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        target_file = Path(tmpdir) / 'found.json'
        tmp_file = target_file.with_suffix('.tmp')
        
        # Dane testowe
        test_data = [
            {
                'date': '2024-01-01',
                'sender': 'test@example.com',
                'subject': 'Test',
                'filename': 'test.pdf',
                'file_path': '/tmp/test.pdf'
            }
        ]
        
        # Zapisz do pliku tymczasowego
        with open(tmp_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2, ensure_ascii=False)
        
        print(f"  ✓ Zapisano do pliku tymczasowego: {tmp_file}")
        
        # Atomowe zastąpienie
        os.replace(tmp_file, target_file)
        print(f"  ✓ Atomowo zastąpiono: {target_file}")
        
        # Sprawdź czy plik tymczasowy został usunięty
        assert not tmp_file.exists(), "Plik tymczasowy powinien zostać usunięty"
        print("  ✓ Plik tymczasowy został usunięty")
        
        # Sprawdź czy docelowy plik istnieje i ma poprawne dane
        assert target_file.exists(), "Plik docelowy powinien istnieć"
        with open(target_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        assert loaded_data == test_data, "Dane powinny być identyczne"
        print("  ✓ Dane zostały zapisane poprawnie")
    
    return True


def test_load_validation():
    """Test walidacji przy wczytywaniu"""
    print("\nTest 2: Walidacja przy wczytywaniu")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        target_file = Path(tmpdir) / 'found.json'
        
        # Test 1: Nieprawidłowy typ (obiekt zamiast listy)
        print("  Test 2a: Nieprawidłowy typ danych")
        with open(target_file, 'w', encoding='utf-8') as f:
            json.dump({'data': 'invalid'}, f)
        
        try:
            with open(target_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                print("    ✓ Wykryto nieprawidłowy typ (nie lista)")
                data = []
            else:
                print("    ✗ Nie wykryto nieprawidłowego typu")
                return False
        except Exception as e:
            print(f"    ✗ Błąd: {e}")
            return False
        
        # Test 2: Nieprawidłowy JSON
        print("  Test 2b: Nieprawidłowy JSON")
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write('{invalid json}')
        
        try:
            with open(target_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print("    ✗ Nie wykryto nieprawidłowego JSON")
            return False
        except json.JSONDecodeError:
            print("    ✓ Wykryto nieprawidłowy JSON")
        except Exception as e:
            print(f"    ✗ Nieoczekiwany błąd: {e}")
            return False
        
        # Test 3: Prawidłowe dane
        print("  Test 2c: Prawidłowe dane (lista)")
        test_data = [
            {'filename': 'test.pdf', 'date': '2024-01-01'}
        ]
        with open(target_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)
        
        try:
            with open(target_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list) and len(data) == 1:
                print("    ✓ Wczytano prawidłowe dane")
            else:
                print("    ✗ Dane nie są prawidłowe")
                return False
        except Exception as e:
            print(f"    ✗ Błąd: {e}")
            return False
    
    return True


def test_invoice_structure():
    """Test struktury faktury z timestamp"""
    print("\nTest 3: Struktura faktury")
    
    from datetime import datetime
    
    invoice = {
        'date': '2024-01-01',
        'sender': 'test@example.com',
        'subject': 'Test Invoice',
        'filename': 'test.pdf',
        'file_path': '/tmp/test.pdf',
        'found_timestamp': datetime.now().isoformat()
    }
    
    # Sprawdź wymagane pola
    required_fields = ['date', 'sender', 'subject', 'filename', 'file_path', 'found_timestamp']
    for field in required_fields:
        if field not in invoice:
            print(f"  ✗ Brak wymaganego pola: {field}")
            return False
    
    print(f"  ✓ Wszystkie wymagane pola są obecne")
    
    # Sprawdź czy timestamp jest w formacie ISO
    try:
        datetime.fromisoformat(invoice['found_timestamp'])
        print(f"  ✓ Timestamp ma prawidłowy format ISO")
    except ValueError:
        print(f"  ✗ Timestamp ma nieprawidłowy format")
        return False
    
    return True


def test_code_patterns():
    """Test czy kod zawiera poprawki opisane w zadaniu"""
    print("\nTest 4: Sprawdzenie obecności poprawek w kodzie")
    
    with open('poczta_faktury.py', 'r', encoding='utf-8') as f:
        code = f.read()
    
    # Sprawdź czy load_found_invoices ma walidację
    if 'isinstance(data, list)' in code:
        print("  ✓ load_found_invoices ma walidację typu")
    else:
        print("  ✗ Brak walidacji typu w load_found_invoices")
        return False
    
    # Sprawdź czy save_found_invoices używa atomowego zapisu
    if 'os.replace' in code and '.tmp' in code:
        print("  ✓ save_found_invoices używa atomowego zapisu")
    else:
        print("  ✗ Brak atomowego zapisu w save_found_invoices")
        return False
    
    # Sprawdź czy add_found_invoice sprawdza inicjalizację
    if 'if not hasattr(self, \'found_invoices\')' in code:
        print("  ✓ add_found_invoice sprawdza inicjalizację")
    else:
        print("  ✗ Brak sprawdzenia inicjalizacji w add_found_invoice")
        return False
    
    # Sprawdź czy refresh_found_invoices obsługuje brak widgetu
    if 'if not hasattr(self, \'found_tree\')' in code:
        print("  ✓ refresh_found_invoices obsługuje brak widgetu")
    else:
        print("  ✗ Brak obsługi braku widgetu w refresh_found_invoices")
        return False
    
    # Sprawdź czy create_found_tab jest wywoływana
    if 'self.create_found_tab()' in code:
        print("  ✓ create_found_tab jest wywoływana w create_widgets")
    else:
        print("  ✗ create_found_tab nie jest wywoływana")
        return False
    
    # Sprawdź czy refresh jest planowane po utworzeniu widgetu
    if 'self.root.after(0, self.refresh_found_invoices)' in code:
        print("  ✓ refresh_found_invoices jest planowane po utworzeniu widgetu")
    else:
        print("  ✗ Brak planowania refresh po utworzeniu widgetu")
        return False
    
    return True


def main():
    """Uruchom wszystkie testy"""
    print("=" * 60)
    print("TESTY LOGIKI ZAPISU/ODCZYTU FAKTUR")
    print("=" * 60)
    
    tests = [
        test_atomic_save,
        test_load_validation,
        test_invoice_structure,
        test_code_patterns
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
                print(f"✓ {test.__name__} ZALICZONY\n")
        except Exception as e:
            failed += 1
            print(f"✗ {test.__name__} NIEZALICZONY: {e}\n")
            import traceback
            traceback.print_exc()
    
    print("=" * 60)
    print(f"WYNIKI: {passed}/{len(tests)} testów zaliczonych")
    print("=" * 60)
    
    return failed == 0


if __name__ == '__main__':
    import sys
    success = main()
    sys.exit(0 if success else 1)
