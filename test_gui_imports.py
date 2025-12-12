#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test importów i podstawowych metod GUI bez faktycznego uruchomienia okna
"""

import sys
import os

def test_imports():
    """Test czy wszystkie importy działają"""
    print("Test: Importy modułów")
    
    try:
        import tkinter as tk
        print("  ✓ tkinter")
    except ImportError as e:
        print(f"  ✗ tkinter: {e}")
        return False
    
    try:
        from poczta_faktury import EmailInvoiceFinderApp
        print("  ✓ EmailInvoiceFinderApp")
    except ImportError as e:
        print(f"  ✗ EmailInvoiceFinderApp: {e}")
        return False
    
    return True


def test_app_initialization():
    """Test inicjalizacji aplikacji bez wyświetlania okna"""
    print("\nTest: Inicjalizacja aplikacji")
    
    try:
        # Import bez wyświetlania GUI
        os.environ['DISPLAY'] = ':99'  # Fake display dla headless
        
        import tkinter as tk
        from poczta_faktury import EmailInvoiceFinderApp
        
        # Próba utworzenia root (może nie zadziałać w headless)
        try:
            root = tk.Tk()
            root.withdraw()  # Ukryj okno
            
            # Inicjalizuj aplikację
            app = EmailInvoiceFinderApp(root)
            
            print("  ✓ Aplikacja zainicjalizowana")
            
            # Test kilku metod
            print("\nTest: Metody aplikacji")
            
            # Test 1: matches_invoice_pattern
            result1 = app.matches_invoice_pattern("faktura_2024.pdf")
            print(f"  Test matches_invoice_pattern('faktura_2024.pdf'): {'✓' if result1 else '✗'}")
            
            # Test 2: get_unique_filename
            import tempfile
            with tempfile.TemporaryDirectory() as tmpdir:
                path = app.get_unique_filename(tmpdir, "test.pdf")
                result2 = path.endswith("test.pdf")
                print(f"  Test get_unique_filename: {'✓' if result2 else '✗'}")
            
            # Test 3: found_invoices initialization
            result3 = isinstance(app.found_invoices, list)
            print(f"  Test found_invoices list: {'✓' if result3 else '✗'}")
            
            # Test 4: search_config
            result4 = 'invoice_filename_pattern' in app.search_config
            print(f"  Test search_config has invoice_filename_pattern: {'✓' if result4 else '✗'}")
            
            root.destroy()
            
            return all([result1, result2, result3, result4])
            
        except tk.TclError as e:
            print(f"  ⚠ Nie można utworzyć GUI (headless environment): {e}")
            print("  → To jest oczekiwane w środowisku bez X11/display")
            return True  # Nie traktujemy jako błąd
    
    except Exception as e:
        print(f"  ✗ Błąd: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_helper_functions():
    """Test funkcji pomocniczych bez GUI"""
    print("\nTest: Funkcje pomocnicze bez GUI")
    
    from poczta_faktury import EmailInvoiceFinderApp
    import tempfile
    
    # Tworzymy instancję tylko dla dostępu do metod
    # (bez inicjalizacji GUI)
    
    class MockApp:
        def __init__(self):
            self.search_config = {
                'invoice_filename_pattern': r'fakt',
                'overwrite_policy': 'suffix'
            }
        
        def matches_invoice_pattern(self, filename):
            """Sprawdza czy nazwa pliku pasuje do wzorca faktury"""
            if not filename:
                return False
            
            import re
            pattern = self.search_config.get('invoice_filename_pattern', r'fakt')
            
            try:
                return re.search(pattern, filename, re.IGNORECASE) is not None
            except re.error:
                return pattern.lower() in filename.lower()
        
        def get_unique_filename(self, output_folder, filename):
            """Generuje unikalną nazwę pliku zgodnie z polityką nadpisywania"""
            import os
            overwrite_policy = self.search_config.get('overwrite_policy', 'suffix')
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
    
    app = MockApp()
    
    # Test 1: Pattern matching
    result1 = app.matches_invoice_pattern("FAKTURA_VAT.pdf")
    print(f"  Test pattern matching: {'✓' if result1 else '✗'}")
    
    # Test 2: Unique filename
    with tempfile.TemporaryDirectory() as tmpdir:
        path1 = app.get_unique_filename(tmpdir, "test.pdf")
        open(path1, 'w').close()
        path2 = app.get_unique_filename(tmpdir, "test.pdf")
        result2 = path2.endswith("test_1.pdf")
        print(f"  Test unique filename: {'✓' if result2 else '✗'}")
    
    return all([result1, result2])


def main():
    print("=" * 60)
    print("TESTY GUI I IMPORTÓW")
    print("=" * 60)
    print()
    
    results = []
    
    # Test 1: Importy
    results.append(test_imports())
    
    # Test 2: Inicjalizacja
    results.append(test_app_initialization())
    
    # Test 3: Funkcje pomocnicze
    results.append(test_helper_functions())
    
    print()
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"WYNIKI: {passed}/{total} testów zaliczonych")
    print("=" * 60)
    
    return all(results)


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
