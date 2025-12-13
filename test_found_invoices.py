#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test dla sprawdzenia poprawek w funkcjonalności Znalezionych faktur
"""

import tkinter as tk
import sys
import os
import json
import tempfile
from pathlib import Path

# Dodaj ścieżkę do importu
sys.path.insert(0, os.path.dirname(__file__))

from poczta_faktury import EmailInvoiceFinderApp, FOUND_INVOICES_FILE


def test_found_invoices_tab_exists():
    """Sprawdza czy zakładka Znalezione faktury istnieje"""
    print("\nTest 1: Sprawdzenie istnienia zakładki 'Znalezione faktury'")
    
    root = tk.Tk()
    try:
        app = EmailInvoiceFinderApp(root)
        
        # Sprawdź czy found_frame istnieje
        assert hasattr(app, 'found_frame'), "Brak atrybutu found_frame"
        print("  ✓ found_frame istnieje")
        
        # Sprawdź czy found_tree istnieje
        assert hasattr(app, 'found_tree'), "Brak atrybutu found_tree"
        print("  ✓ found_tree istnieje")
        
        # Sprawdź liczbę zakładek (powinno być 4: Konfiguracja, Wyszukiwanie, Znalezione faktury, O programie)
        tab_count = app.notebook.index('end')
        assert tab_count == 4, f"Oczekiwano 4 zakładek, znaleziono {tab_count}"
        print(f"  ✓ Liczba zakładek: {tab_count}")
        
        # Sprawdź nazwę trzeciej zakładki
        tab_text = app.notebook.tab(2, 'text')
        assert tab_text == "Znalezione faktury", f"Oczekiwano 'Znalezione faktury', znaleziono '{tab_text}'"
        print(f"  ✓ Nazwa trzeciej zakładki: '{tab_text}'")
        
        return True
        
    finally:
        root.destroy()


def test_load_found_invoices_validation():
    """Test walidacji przy wczytywaniu znalezionych faktur"""
    print("\nTest 2: Walidacja danych przy wczytywaniu")
    
    # Utwórz tymczasowy plik z nieprawidłowymi danymi
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_file = Path(tmpdir) / 'test_found.json'
        
        # Test 1: Nieprawidłowy JSON (nie lista)
        print("  Test 2a: Nieprawidłowy typ danych (obiekt zamiast listy)")
        with open(tmp_file, 'w') as f:
            json.dump({'data': 'invalid'}, f)
        
        # Podmień ścieżkę
        import poczta_faktury
        original_file = poczta_faktury.FOUND_INVOICES_FILE
        poczta_faktury.FOUND_INVOICES_FILE = tmp_file
        
        try:
            root = tk.Tk()
            app = EmailInvoiceFinderApp(root)
            
            # Powinno zainicjalizować pustą listę
            assert isinstance(app.found_invoices, list), "found_invoices powinno być listą"
            assert len(app.found_invoices) == 0, "found_invoices powinno być puste"
            print("    ✓ Nieprawidłowe dane zostały zignorowane")
            
            root.destroy()
        finally:
            poczta_faktury.FOUND_INVOICES_FILE = original_file
        
        # Test 2: Prawidłowe dane
        print("  Test 2b: Prawidłowe dane")
        test_data = [
            {
                'date': '2024-01-01',
                'sender': 'test@example.com',
                'subject': 'Test',
                'filename': 'test.pdf',
                'file_path': '/tmp/test.pdf',
                'found_timestamp': '2024-01-01T12:00:00'
            }
        ]
        with open(tmp_file, 'w') as f:
            json.dump(test_data, f)
        
        poczta_faktury.FOUND_INVOICES_FILE = tmp_file
        
        try:
            root = tk.Tk()
            app = EmailInvoiceFinderApp(root)
            
            assert len(app.found_invoices) == 1, "Powinno wczytać 1 fakturę"
            assert app.found_invoices[0]['filename'] == 'test.pdf', "Nieprawidłowa nazwa pliku"
            print("    ✓ Prawidłowe dane zostały wczytane")
            
            root.destroy()
        finally:
            poczta_faktury.FOUND_INVOICES_FILE = original_file
    
    return True


def test_save_found_invoices_atomic():
    """Test atomowego zapisu znalezionych faktur"""
    print("\nTest 3: Atomowy zapis danych")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_file = Path(tmpdir) / 'test_found.json'
        
        import poczta_faktury
        original_file = poczta_faktury.FOUND_INVOICES_FILE
        poczta_faktury.FOUND_INVOICES_FILE = tmp_file
        
        try:
            root = tk.Tk()
            app = EmailInvoiceFinderApp(root)
            
            # Dodaj fakturę
            app.add_found_invoice(
                date='2024-01-01',
                sender='test@example.com',
                subject='Test Invoice',
                filename='test.pdf',
                file_path='/tmp/test.pdf'
            )
            
            # Sprawdź czy plik został utworzony
            assert tmp_file.exists(), "Plik powinien zostać utworzony"
            print("  ✓ Plik został utworzony")
            
            # Sprawdź czy plik tymczasowy został usunięty
            tmp_tmp_file = tmp_file.with_suffix('.tmp')
            assert not tmp_tmp_file.exists(), "Plik tymczasowy powinien zostać usunięty"
            print("  ✓ Plik tymczasowy został usunięty")
            
            # Sprawdź zawartość
            with open(tmp_file, 'r') as f:
                data = json.load(f)
            
            assert len(data) == 1, "Powinien być 1 wpis"
            assert data[0]['filename'] == 'test.pdf', "Nieprawidłowa nazwa pliku"
            assert 'found_timestamp' in data[0], "Brak timestampu"
            print("  ✓ Dane zostały zapisane poprawnie")
            
            root.destroy()
        finally:
            poczta_faktury.FOUND_INVOICES_FILE = original_file
    
    return True


def test_refresh_found_invoices_resilience():
    """Test odporności refresh_found_invoices na brak widgetu"""
    print("\nTest 4: Odporność refresh_found_invoices")
    
    root = tk.Tk()
    try:
        app = EmailInvoiceFinderApp(root)
        
        # Dodaj testową fakturę
        app.found_invoices = [
            {
                'date': '2024-01-01',
                'sender': 'test@example.com',
                'subject': 'Test',
                'filename': 'test.pdf',
                'file_path': '/tmp/test.pdf'
            }
        ]
        
        # Wywołaj refresh - powinno zadziałać
        app.refresh_found_invoices()
        
        # Sprawdź czy dane zostały dodane do drzewa
        items = app.found_tree.get_children()
        assert len(items) == 1, "Powinien być 1 element w drzewie"
        print("  ✓ refresh_found_invoices działa poprawnie")
        
        # Sprawdź wartości
        values = app.found_tree.item(items[0], 'values')
        assert values[3] == 'test.pdf', "Nieprawidłowa nazwa pliku w drzewie"
        print("  ✓ Dane zostały poprawnie wyświetlone")
        
        return True
        
    finally:
        root.destroy()


def main():
    """Uruchom wszystkie testy"""
    print("=" * 60)
    print("TESTY POPRAWEK ZNALEZIONYCH FAKTUR")
    print("=" * 60)
    
    tests = [
        test_found_invoices_tab_exists,
        test_load_found_invoices_validation,
        test_save_found_invoices_atomic,
        test_refresh_found_invoices_resilience
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
                print(f"  ✓ {test.__name__} ZALICZONY")
        except Exception as e:
            failed += 1
            print(f"  ✗ {test.__name__} NIEZALICZONY: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"WYNIKI: {passed}/{len(tests)} testów zaliczonych")
    print("=" * 60)
    
    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
