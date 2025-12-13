#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test for auto-refresh behavior when adding found invoices
"""

import tkinter as tk
import sys
import os
import tempfile
from pathlib import Path

# Dodaj ścieżkę do importu
sys.path.insert(0, os.path.dirname(__file__))

from poczta_faktury import EmailInvoiceFinderApp
import poczta_faktury


def test_auto_refresh_on_add_invoice():
    """Sprawdza czy dodanie faktury automatycznie odświeża treeview"""
    print("\nTest: Automatyczne odświeżanie po dodaniu faktury")
    
    # Use temporary file for testing to avoid interfering with persistent data
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_file = Path(tmpdir) / 'test_found.json'
        original_file = poczta_faktury.FOUND_INVOICES_FILE
        poczta_faktury.FOUND_INVOICES_FILE = tmp_file
        
        try:
            root = tk.Tk()
            try:
                app = EmailInvoiceFinderApp(root)
                
                # Sprawdź że tabela jest początkowo pusta
                initial_items = app.found_tree.get_children()
                assert len(initial_items) == 0, f"Tabela powinna być początkowo pusta, zawiera {len(initial_items)}"
                print("  ✓ Początkowa tabela jest pusta")
                
                # Dodaj fakturę - powinno to automatycznie odświeżyć GUI
                app.add_found_invoice(
                    date='2024-12-13',
                    sender='test@example.com',
                    subject='Test Invoice',
                    filename='test_invoice.pdf',
                    file_path='/tmp/test_invoice.pdf'
                )
                
                # Poczekaj na wykonanie wszystkich zaplanowanych zadań (including root.after(0, ...))
                root.update()
                
                # Sprawdź czy faktura jest teraz widoczna w tabeli
                items = app.found_tree.get_children()
                assert len(items) == 1, f"Tabela powinna zawierać 1 element, zawiera {len(items)}"
                print("  ✓ Faktura została automatycznie dodana do tabeli")
                
                # Sprawdź wartości faktury
                values = app.found_tree.item(items[0], 'values')
                assert values[0] == '2024-12-13', f"Nieprawidłowa data: {values[0]}"
                assert values[1] == 'test@example.com', f"Nieprawidłowy nadawca: {values[1]}"
                assert values[2] == 'Test Invoice', f"Nieprawidłowy temat: {values[2]}"
                assert values[3] == 'test_invoice.pdf', f"Nieprawidłowa nazwa pliku: {values[3]}"
                print("  ✓ Wartości faktury są poprawne")
                
                # Dodaj drugą fakturę
                app.add_found_invoice(
                    date='2024-12-14',
                    sender='test2@example.com',
                    subject='Second Invoice',
                    filename='test_invoice_2.pdf',
                    file_path='/tmp/test_invoice_2.pdf'
                )
                
                # Poczekaj na wykonanie wszystkich zaplanowanych zadań
                root.update()
                
                # Sprawdź czy obie faktury są widoczne
                items = app.found_tree.get_children()
                assert len(items) == 2, f"Tabela powinna zawierać 2 elementy, zawiera {len(items)}"
                print("  ✓ Druga faktura została automatycznie dodana do tabeli")
                
                # Sprawdź że obie faktury są poprawne
                values_1 = app.found_tree.item(items[0], 'values')
                values_2 = app.found_tree.item(items[1], 'values')
                assert values_1[3] == 'test_invoice.pdf', "Pierwsza faktura niepoprawna"
                assert values_2[3] == 'test_invoice_2.pdf', "Druga faktura niepoprawna"
                print("  ✓ Obie faktury są poprawnie wyświetlone")
                
                return True
                
            finally:
                root.destroy()
        finally:
            poczta_faktury.FOUND_INVOICES_FILE = original_file


def test_auto_refresh_is_thread_safe():
    """Sprawdza czy auto-refresh nie powoduje błędów przy zniszczonym oknie"""
    print("\nTest: Bezpieczeństwo wątków przy auto-refresh")
    
    root = tk.Tk()
    app = EmailInvoiceFinderApp(root)
    
    # Zniszcz okno
    root.destroy()
    
    # Próba dodania faktury nie powinna wywołać błędu
    try:
        app.add_found_invoice(
            date='2024-12-13',
            sender='test@example.com',
            subject='Test Invoice',
            filename='test.pdf',
            file_path='/tmp/test.pdf'
        )
        print("  ✓ Brak błędu przy dodawaniu faktury po zniszczeniu okna")
        return True
    except Exception as e:
        print(f"  ✗ Błąd przy dodawaniu faktury: {e}")
        return False


def main():
    """Uruchom wszystkie testy"""
    print("=" * 60)
    print("TESTY AUTO-REFRESH ZNALEZIONYCH FAKTUR")
    print("=" * 60)
    
    tests = [
        test_auto_refresh_on_add_invoice,
        test_auto_refresh_is_thread_safe
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
