# Poczta-Faktury
Wyszukiwanie faktur po numerze NIP w załącznikach email

## Opis

Aplikacja z interfejsem graficznym (GUI) umożliwiająca:
- Konfigurację dostępu do poczty email (POP3, IMAP, Exchange)
- Wyszukiwanie faktur w załącznikach PDF po numerze NIP
- Automatyczny zapis znalezionych faktur do wskazanego folderu

## Wymagania

- Python 3.7 lub nowszy
- Biblioteki wymienione w `requirements.txt`

## Instalacja

1. Sklonuj repozytorium:
```bash
git clone https://github.com/dzieju/Poczta-Faktury.git
cd Poczta-Faktury
```

2. Zainstaluj wymagane biblioteki:
```bash
pip install -r requirements.txt
```

## Użycie

1. Uruchom aplikację:
```bash
python main.py
```

**Wersjonowanie**: Aplikacja wyświetla wersję w tytule okna, która jest pobierana z pliku `version.txt`. Wersja jest automatycznie zwiększana przez GitHub Actions workflow przy każdym push do gałęzi `main` (patch version jest inkrementowana).

2. W zakładce "Ustawienia":
   - Wybierz protokół (IMAP, POP3 lub Exchange)
   - Podaj adres serwera email (np. imap.gmail.com)
   - Podaj port (domyślnie 993 dla IMAP SSL)
   - Wprowadź adres email i hasło
   - Zaznacz "Użyj SSL/TLS" jeśli wymagane
   - Opcjonalnie zaznacz "Pokaż hasło" aby zobaczyć wpisywane hasło
   - Opcjonalnie zaznacz "Zapisz ustawienia" aby zapisać konfigurację do pliku ~/.poczta_faktury_config.json
   - Kliknij "Testuj połączenie" aby sprawdzić poprawność konfiguracji

3. W zakładce "Wyszukiwanie NIP":
   - Wprowadź numer NIP do wyszukania
   - Wybierz folder, w którym mają być zapisane znalezione faktury
   - **Zakres czasowy - wybierz jedną z opcji:**
     - Opcjonalnie wybierz zakres przeszukiwania (1 miesiąc, 3 miesiące, 6 miesięcy lub ostatni tydzień)
     - **LUB** użyj własnego zakresu dat za pomocą kalendarzy "Od" i "Do":
       - Kliknij w pole "Od" aby wybrać datę początkową (opcjonalnie)
       - Kliknij w pole "Do" aby wybrać datę końcową (domyślnie: dzisiaj)
       - Data "Od" musi być wcześniejsza lub równa dacie "Do"
       - Kliknij "Wyczyść zakres" aby zresetować daty
       - Wybrany zakres będzie wyświetlony nad paskiem postępu
   - Opcjonalnie zaznacz "Zapisz ustawienia" aby zapisać preferencje
   - Kliknij "Szukaj faktur"
   - Podczas wyszukiwania możesz kliknąć "Przerwij" aby zatrzymać operację

4. Aplikacja przeszuka wszystkie załączniki PDF w skrzynce email i zapisze te, które zawierają podany numer NIP.
   - Wyszukiwanie działa w tle - GUI pozostaje responsywne
   - Logi i postęp są wyświetlane w czasie rzeczywistym
   - Zapisane pliki mają datę modyfikacji ustawioną zgodnie z datą otrzymania emaila

**Uwaga**: Ustawienia aplikacji są zapisywane w pliku `~/.poczta_faktury_config.json` (jeśli zaznaczono opcję "Zapisz ustawienia"). Hasło do poczty jest zapisywane tylko gdy zaznaczysz checkbox "Zapisz ustawienia" w zakładce "Ustawienia".

## Przykładowe konfiguracje serwerów

### Gmail
- Protokół: IMAP
- Serwer: imap.gmail.com
- Port: 993
- SSL: TAK
- Uwaga: Może wymagać hasła aplikacji zamiast zwykłego hasła

### Outlook/Hotmail
- Protokół: IMAP
- Serwer: outlook.office365.com
- Port: 993
- SSL: TAK

### Exchange
- Protokół: Exchange (IMAP)
- Serwer: adres serwera Exchange
- Port: 993 (lub inny zgodnie z konfiguracją)
- SSL: TAK (zazwyczaj)

## Funkcje

- ✅ Obsługa protokołów POP3, IMAP i Exchange (przez IMAP)
- ✅ Wyszukiwanie numerów NIP w załącznikach PDF
- ✅ Automatyczny zapis znalezionych faktur
- ✅ Interfejs graficzny w języku polskim
- ✅ Nieblokujące wyszukiwanie - GUI pozostaje responsywne podczas operacji
- ✅ Przycisk "Przerwij" do zatrzymania wyszukiwania w dowolnym momencie
- ✅ Pasek postępu i informacje o przebiegu wyszukiwania w czasie rzeczywistym
- ✅ Obsługa różnych formatów zapisu NIP (z kreskami i bez)
- ✅ Możliwość zapisania ustawień do pliku konfiguracyjnego
- ✅ Filtrowanie wiadomości według zakresu czasowego (1/3/6 miesięcy lub ostatni tydzień)
- ✅ **Własny zakres dat z kalendarzem "Od - Do"** - precyzyjne określenie zakresu przeszukiwania
- ✅ Przełączanie widoczności hasła
- ✅ Ustawianie daty modyfikacji plików zgodnie z datą otrzymania emaila
- ✅ Zakładka "O programie" z danymi kontaktowymi i wersją aplikacji
- ✅ Automatyczne wersjonowanie aplikacji (patch version zwiększana przy każdym push do main)
- ✅ Okno "Znalezione" - zaawansowane wyniki wyszukiwania z tabelą wiadomości i podglądem dopasowań PDF

## Okno "Znalezione" - Zaawansowane wyniki wyszukiwania

Aplikacja zawiera nowe okno "Znalezione", które oferuje zaawansowany widok wyników wyszukiwania. Funkcjonalność ta została zaimplementowana przy użyciu komponentów skopiowanych z repozytorium [dzieju-app2](https://github.com/dzieju/dzieju-app2):

### Menu kontekstowe (PPM)

Okno wyników wyszukiwania obsługuje menu kontekstowe (prawy przycisk myszy), które pozwala na:
- **Otwórz PDF** - otwiera plik PDF faktuty w domyślnej aplikacji systemowej (np. Adobe Reader, Foxit, przeglądarka)
- **Otwórz Email** - otwiera plik .eml w domyślnym kliencie poczty (np. Outlook, Thunderbird)

Menu kontekstowe:
- Wyświetla tylko dostępne opcje (jeśli nie ma pliku EML, pokazuje tylko "Otwórz PDF")
- Automatycznie wykrywa dostępność plików przed wyświetleniem menu
- Pokazuje szczegółowe komunikaty błędów ze ścieżką do pliku w przypadku problemów
- Obsługuje klawisze: prawy przycisk myszy (Windows/Linux), Ctrl+klik (macOS)

### Skopiowane komponenty

1. **gui/imap_search_components/pdf_processor.py** - Ekstrakcja tekstu z PDF i OCR
   - Źródło: [pdf_processor.py](https://github.com/dzieju/dzieju-app2/blob/fcee6b91bf240d17ceb38f8564beab5aa9637437/gui/imap_search_components/pdf_processor.py)
   - Funkcje: Ekstrakcja tekstu z PDF, OCR fallback, normalizacja tekstu (usuwanie spacji/kresek)
   - Metoda `_extract_matches` zwraca fragmenty tekstu z kontekstem wokół dopasowań

2. **gui/imap_search_components/search_engine.py** - Silnik wyszukiwania email
   - Źródło: [search_engine.py (IMAP)](https://github.com/dzieju/dzieju-app2/blob/fcee6b91bf240d17ceb38f8564beab5aa9637437/gui/imap_search_components/search_engine.py)
   - Funkcje: Wyszukiwanie wiadomości, paginacja, mapowanie wiadomość->folder
   - Publiczne API: `search_messages(criteria, progress_callback)`

3. **gui/mail_search_components/exchange_connection.py** - Zarządzanie folderami Exchange
   - Źródło: [exchange_connection.py](https://github.com/dzieju/dzieju-app2/blob/fcee6b91bf240d17ceb38f8564beab5aa9637437/gui/mail_search_components/exchange_connection.py)
   - Funkcje: `_get_all_subfolders_recursive`, `get_available_folders_for_exclusion`
   - Używane do odkrywania struktury folderów w skrzynce pocztowej

4. **gui/search_results/znalezione_window.py** - Okno GUI z wynikami
   - Nowa implementacja oparta na Tkinter
   - Tabela z kolumnami: data, nadawca, temat, folder, załączniki, status
   - Podgląd dopasowań PDF z kontekstem
   - Przyciski akcji: Otwórz załącznik, Pobierz, Pokaż w poczcie
   - Paginacja wyników

### Jak używać okna "Znalezione"

1. W zakładce "Wyszukiwanie NIP" wprowadź numer NIP i opcjonalnie wybierz zakres dat
2. Kliknij przycisk "Znalezione ➜" obok przycisku "Szukaj faktur"
3. Otworzy się nowe okno z zaawansowanym interfejsem wyników
4. Aby otworzyć pliki:
   - **Podwójne kliknięcie** na wynik - otwiera PDF
   - **Prawy przycisk myszy** (PPM) na wynik - pokazuje menu z opcjami "Otwórz PDF" i "Otwórz Email"
   - **Przyciski akcji** na dole - "Otwórz załącznik" i "Pokaż w poczcie"

### Testy jednostkowe

Dodano testy dla metody `_extract_matches`:
- `tests/test_pdf_extract_matches.py` - 11 przypadków testowych
- Testowanie dopasowań: dokładne, przybliżone (z normalizacją), case-insensitive
- Testowanie różnych formatów NIP (z kreskami, spacjami, różnymi separatorami)

Uruchom testy: `python tests/test_pdf_extract_matches.py`

## Własny zakres dat (Kalendarz "Od - Do")

Aplikacja oferuje zaawansowane filtrowanie wiadomości email według daty za pomocą kalendarzy "Od" i "Do" w sekcji "Własny zakres dat".

### Jak używać kalendarzy dat

1. **Wybór daty początkowej (Od)**:
   - Kliknij w pole "Od" aby otworzyć kalendarz
   - Wybierz datę początkową zakresu
   - Pole może pozostać puste jeśli chcesz szukać od początku

2. **Wybór daty końcowej (Do)**:
   - Kliknij w pole "Do" aby otworzyć kalendarz
   - Wybierz datę końcową zakresu (domyślnie: dzisiejsza data)
   - Data końcowa włącznie jest uwzględniana w wyszukiwaniu

3. **Czyszczenie zakresu**:
   - Kliknij przycisk "Wyczyść zakres" aby zresetować daty do wartości domyślnych
   - Po wyczyszczeniu: "Od" = puste, "Do" = dzisiaj

### Walidacja zakresu dat

- **Data "Od" nie może być późniejsza niż data "Do"**
  - Jeśli wybierzesz nieprawidłowy zakres, zobaczysz komunikat błędu
  - Wyszukiwanie zostanie zablokowane dopóki nie poprawisz zakresu

- **Wybrany zakres jest wyświetlany**
  - Nad paskiem postępu zobaczysz wybrany zakres, np. "Wybrany zakres: Od 2025-01-01 Do 2025-12-31"
  - Pomaga to w potwierdzeniu poprawności wybranego zakresu

### Priorytet zakresów

- Jeśli wybierzesz **własny zakres dat** (Od/Do), będzie on miał priorytet nad checkboxami (1/3/6 miesięcy)
- Jeśli **nie wybierzesz własnego zakresu**, zostaną użyte checkboxy
- Jeśli **nie wybierzesz żadnego zakresu**, przeszukiwane będą wszystkie wiadomości

### Format daty

- Format daty: **YYYY-MM-DD** (ISO 8601)
- Przykład: 2025-12-16
- Format jest zgodny ze standardem IMAP i ułatwia sortowanie

### Przykłady użycia

1. **Szukaj faktur z ostatniego miesiąca**:
   - Od: 2025-11-16 (miesiąc temu)
   - Do: 2025-12-16 (dzisiaj)

2. **Szukaj faktur z konkretnego kwartału**:
   - Od: 2025-01-01
   - Do: 2025-03-31

3. **Szukaj faktur do określonej daty**:
   - Od: (puste)
   - Do: 2025-06-30

4. **Szukaj faktur od określonej daty do dziś**:
   - Od: 2025-06-01
   - Do: (dzisiejsza data)

### Zapisywanie zakresu dat

- Wybrane daty mogą być zapisane w konfiguracji
- Zaznacz checkbox "Zapisz ustawienia" aby zapisać zakres dat
- Zakres będzie automatycznie przywrócony przy następnym uruchomieniu aplikacji

## Uwagi

- Aplikacja wymaga dostępu do internetu
- Wyszukiwanie dużej liczby wiadomości może zająć kilka minut
- Możesz użyć przycisku "Przerwij" aby zatrzymać wyszukiwanie w dowolnym momencie
- Niektóre serwery email mogą wymagać specjalnych uprawnień lub haseł aplikacji
- Daty modyfikacji zapisanych plików odpowiadają dacie otrzymania emaila (sprawdź z `ls -l --time-style=long-iso`)
- Okno "Znalezione" jest w wersji demonstracyjnej - pełna integracja z wyszukiwaniem wymaga dalszej implementacji
