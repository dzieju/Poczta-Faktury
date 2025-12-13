#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt do manualnego testowania aplikacji (wymaga środowiska graficznego)
"""

import sys
import json
from pathlib import Path

# Symulacja środowiska do testowania logiki
def simulate_app_lifecycle():
    """Symuluje cykl życia aplikacji bez GUI"""
    print("=" * 60)
    print("SYMULACJA CYKLU ŻYCIA APLIKACJI")
    print("=" * 60)
    
    # Utwórz testowy plik z fakturami
    test_file = Path.home() / '.poczta_faktury_found_test.json'
    
    test_invoices = [
        {
            'date': '2024-01-15 10:30',
            'sender': 'kontakt@firmaabc.pl',
            'subject': 'Faktura VAT 2024/01/001',
            'filename': 'faktura_2024_01_001.pdf',
            'file_path': '/tmp/faktura_2024_01_001.pdf',
            'found_timestamp': '2024-01-15T10:30:00'
        },
        {
            'date': '2024-01-20 14:15',
            'sender': 'biuro@firmaxyz.pl',
            'subject': 'Faktura VAT 2024/01/002',
            'filename': 'faktura_2024_01_002.pdf',
            'file_path': '/tmp/faktura_2024_01_002.pdf',
            'found_timestamp': '2024-01-20T14:15:00'
        }
    ]
    
    print(f"\n1. Tworzenie testowego pliku: {test_file}")
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_invoices, f, indent=2, ensure_ascii=False)
    print(f"   ✓ Utworzono plik z {len(test_invoices)} fakturami")
    
    print(f"\n2. Wczytywanie danych z pliku")
    with open(test_file, 'r', encoding='utf-8') as f:
        loaded_data = json.load(f)
    
    if isinstance(loaded_data, list):
        print(f"   ✓ Dane są listą")
        print(f"   ✓ Wczytano {len(loaded_data)} faktur")
    else:
        print(f"   ✗ Dane nie są listą!")
        return False
    
    print(f"\n3. Walidacja struktury faktur")
    required_fields = ['date', 'sender', 'subject', 'filename', 'file_path', 'found_timestamp']
    for i, invoice in enumerate(loaded_data, 1):
        missing_fields = [f for f in required_fields if f not in invoice]
        if missing_fields:
            print(f"   ✗ Faktura {i}: Brakujące pola: {missing_fields}")
            return False
        print(f"   ✓ Faktura {i}: {invoice['filename']} - wszystkie pola obecne")
    
    print(f"\n4. Test atomowego zapisu")
    # Dodaj nową fakturę
    new_invoice = {
        'date': '2024-01-25 16:00',
        'sender': 'info@firma123.pl',
        'subject': 'Faktura VAT 2024/01/003',
        'filename': 'faktura_2024_01_003.pdf',
        'file_path': '/tmp/faktura_2024_01_003.pdf',
        'found_timestamp': '2024-01-25T16:00:00'
    }
    loaded_data.append(new_invoice)
    
    # Atomowy zapis
    tmp_file = test_file.with_suffix('.tmp')
    with open(tmp_file, 'w', encoding='utf-8') as f:
        json.dump(loaded_data, f, indent=2, ensure_ascii=False)
    
    import os
    os.replace(tmp_file, test_file)
    print(f"   ✓ Atomowo zapisano {len(loaded_data)} faktur")
    
    # Sprawdź czy tmp file został usunięty
    if not tmp_file.exists():
        print(f"   ✓ Plik tymczasowy został usunięty")
    else:
        print(f"   ✗ Plik tymczasowy nadal istnieje!")
        return False
    
    print(f"\n5. Ponowne wczytanie i weryfikacja")
    with open(test_file, 'r', encoding='utf-8') as f:
        reloaded_data = json.load(f)
    
    if len(reloaded_data) == 3:
        print(f"   ✓ Wczytano {len(reloaded_data)} faktury (3 oczekiwane)")
    else:
        print(f"   ✗ Wczytano {len(reloaded_data)} faktur, oczekiwano 3")
        return False
    
    print(f"\n6. Czyszczenie")
    test_file.unlink()
    print(f"   ✓ Usunięto testowy plik")
    
    print("\n" + "=" * 60)
    print("SYMULACJA ZAKOŃCZONA SUKCESEM")
    print("=" * 60)
    
    return True


def print_instructions():
    """Wyświetl instrukcje dla manualnego testowania z GUI"""
    print("\n" + "=" * 60)
    print("INSTRUKCJE MANUALNEGO TESTOWANIA (wymaga GUI)")
    print("=" * 60)
    print("""
1. Uruchom aplikację:
   python main.py
   
2. Sprawdź strukturę zakładek:
   - Zakładka 1: "Konfiguracja poczty"
   - Zakładka 2: "Wyszukiwanie NIP"
   - Zakładka 3: "Znalezione faktury" ← NOWA ZAKŁADKA
   - Zakładka 4: "O programie"
   
3. Przejdź do zakładki "Znalezione faktury":
   - Powinny być widoczne przyciski: "Odśwież" i "Wyczyść wszystko"
   - Powinna być widoczna tabela z kolumnami: Data, Nadawca, Temat, Nazwa Pliku
   - Jeśli wcześniej przeprowadzono wyszukiwanie, faktury powinny być widoczne
   
4. Test dodawania faktury:
   - Skonfiguruj połączenie email w zakładce "Konfiguracja poczty"
   - Przejdź do "Wyszukiwanie NIP"
   - Wprowadź NIP i folder zapisu
   - Kliknij "Szukaj faktur"
   - Podczas wyszukiwania sprawdź zakładkę "Znalezione" (live updates)
   - Po zakończeniu wyszukiwania przejdź do "Znalezione faktury"
   - Faktury powinny być widoczne w tabeli
   
5. Test persistencji:
   - Zamknij aplikację
   - Sprawdź plik: ~/.poczta_faktury_found.json
   - Plik powinien zawierać listę znalezionych faktur
   - Uruchom aplikację ponownie
   - Przejdź do zakładki "Znalezione faktury"
   - Faktury z poprzedniego uruchomienia powinny być widoczne
   
6. Test atomowego zapisu:
   - Podczas wyszukiwania sprawdź czy powstaje plik .tmp
   - Po zapisie plik .tmp powinien zniknąć
   - Tylko plik .json powinien pozostać
   
7. Test obsługi błędów:
   - Ręcznie zmodyfikuj plik ~/.poczta_faktury_found.json na nieprawidłowy JSON
   - Uruchom aplikację
   - Aplikacja powinna załadować pustą listę i pokazać komunikat w konsoli
   - Nie powinno wystąpić crashowanie aplikacji
""")
    print("=" * 60)


def main():
    """Główna funkcja testowa"""
    # Uruchom symulację
    success = simulate_app_lifecycle()
    
    # Wyświetl instrukcje
    print_instructions()
    
    return success


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
