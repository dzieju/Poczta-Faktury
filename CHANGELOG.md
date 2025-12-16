# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Changed - 2025-12-16

#### Przeniesienie wyświetlania silnika PDF do zakładki Ustawienia

Wyświetlanie aktualnego silnika PDF zostało przeniesione z okna "Znalezione" do zakładki "Ustawienia" dla lepszej organizacji interfejsu użytkownika.

**Zmiany:**
- Usunięto wyświetlanie "Silnik PDF: {nazwa}" z paska narzędzi okna "Znalezione"
- Dodano wyświetlanie aktualnego silnika obok nagłówka "Silnik PDF:" w zakładce Ustawienia
- Wartość aktualizuje się na żywo przy zmianie wyboru w dropdown menu
- Poprawiono synchronizację między UI a modelem danych (`email_config`)

**Pliki zmienione:**
- `poczta_faktury.py` - dodano `current_engine_label` i callback `_on_pdf_engine_changed()`
- `gui/search_results/znalezione_window.py` - usunięto `pdf_engine_label` i metodę `_get_pdf_engine_from_config()`

**Korzyści:**
- Bardziej logiczne umiejscowienie - wyświetlanie i zmiana silnika w jednym miejscu
- Czystszy interfejs okna wyników wyszukiwania
- Lepsza spójność UI

### Added - 2024-12-14

#### Okno "Znalezione" - Zaawansowane wyniki wyszukiwania

Dodano nowe okno "Znalezione" z zaawansowanym interfejsem do przeglądania wyników wyszukiwania faktur. Funkcjonalność została zaimplementowana poprzez kopiowanie sprawdzonych komponentów z repozytorium [dzieju-app2](https://github.com/dzieju/dzieju-app2).

**Nowe komponenty:**

1. **gui/imap_search_components/pdf_processor.py**
   - Źródło: https://github.com/dzieju/dzieju-app2/blob/fcee6b91bf240d17ceb38f8564beab5aa9637437/gui/imap_search_components/pdf_processor.py
   - Ekstrakcja tekstu z plików PDF za pomocą pdfplumber
   - Fallback do OCR (Tesseract) dla zeskanowanych dokumentów
   - Metoda `_extract_matches()` z normalizacją tekstu (usuwanie spacji, kresek, etc.)
   - Wyświetlanie fragmentów tekstu z kontekstem wokół dopasowań

2. **gui/imap_search_components/search_engine.py**
   - Źródło: https://github.com/dzieju/dzieju-app2/blob/fcee6b91bf240d17ceb38f8564beab5aa9637437/gui/imap_search_components/search_engine.py
   - Silnik wyszukiwania email w wątkach (non-blocking)
   - Publiczne API: `search_messages(criteria, progress_callback)`
   - Struktura zwracana: messages, message_to_folder_map, matches, folder_results
   - Paginacja wyników (per_page, page)

3. **gui/mail_search_components/exchange_connection.py**
   - Źródło: https://github.com/dzieju/dzieju-app2/blob/fcee6b91bf240d17ceb38f8564beab5aa9637437/gui/mail_search_components/exchange_connection.py
   - Zarządzanie połączeniem z serwerem Exchange
   - Metoda `_get_all_subfolders_recursive()` - rekursywne odkrywanie podfolderów
   - Metoda `get_available_folders_for_exclusion()` - lista folderów do wykluczenia
   - Wsparcie dla przycisku "Wykryj foldery"

4. **gui/search_results/znalezione_window.py**
   - Nowe okno GUI zbudowane w Tkinter
   - Tabela wyników z kolumnami: data, nadawca, temat, folder, załączniki, status
   - Podgląd dopasowań PDF z fragmentami tekstu
   - Przyciski akcji: "Otwórz załącznik", "Pobierz", "Pokaż w poczcie"
   - Paginacja wyników
   - Cache dla wyników OCR (unikanie ponownego przetwarzania)

5. **gui/logger.py**
   - Prosty moduł logowania dla komponentów GUI
   - Integracja z istniejącym systemem logowania projektu

**Testy:**

- **tests/test_pdf_extract_matches.py** - 11 przypadków testowych
  - Dokładne dopasowania tekstowe
  - Dopasowania case-insensitive
  - Wiele wystąpień
  - Normalizacja (spacje, kreski, różne separatory)
  - Dopasowania przybliżone
  - Ekstrakcja kontekstu wokół dopasowań
  - Limit wyników (max 5 dopasowań)

**Integracja z główną aplikacją:**

- Przycisk "Znalezione ➜" w zakładce "Wyszukiwanie NIP"
- Automatyczne przekazywanie kryteriów wyszukiwania (NIP, zakres dat)
- Metoda `open_znalezione_window()` w głównej klasie aplikacji

**Dokumentacja:**

- Aktualizacja README.md z opisem nowej funkcjonalności
- Dodanie sekcji o skopiowanych komponentach i ich źródłach
- Instrukcja użycia okna "Znalezione"
- Komentarze w kodzie z linkami do oryginalnych plików

**Dodatkowe pliki:**

- demo_znalezione.py - skrypt demonstracyjny pokazujący użycie nowych komponentów
- Aktualizacja requirements.txt z opcjonalnymi zależnościami (OCR, Exchange)

**Uwagi techniczne:**

- Zachowano oryginalne licencje i nagłówki (gdzie występowały)
- Minimalne zmiany w istniejącym kodzie (tylko dodanie przycisku i metody)
- Nie modyfikowano istniejących obiektów Message
- Użyto mapowania message_to_folder_map zgodnie z oryginalnym kodem
- Wszystkie nowe komponenty mają atrybuty źródłowe w komentarzach
