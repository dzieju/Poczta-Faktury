# Manual Testing Guide - Recursive Folder Search & Found Tab

## Przygotowanie do testów

### Wymagania
1. Python 3.7+
2. Zainstalowane zależności: `pip install -r requirements.txt`
3. Konto email z dostępem IMAP (np. Gmail, Outlook)
4. Kilka wiadomości email z załącznikami PDF (najlepiej w różnych folderach)

### Konfiguracja testowa
1. W ustawieniach konta email utwórz kilka folderów testowych:
   - `Test/Faktury`
   - `Test/Archiwum`
   - `Test/Podfolders/Deep`
2. Przenieś kilka wiadomości z załącznikami PDF do tych folderów
3. Przygotuj pliki PDF z nazwami zawierającymi "faktura", "fakt", "invoice"

## Testy funkcjonalne

### Test 1: Rekursywne przeszukiwanie folderów

**Cel:** Sprawdzenie czy aplikacja przeszukuje wszystkie foldery

**Kroki:**
1. Uruchom aplikację: `python main.py`
2. Skonfiguruj połączenie email w zakładce "Konfiguracja poczty"
3. Kliknij "Testuj połączenie" - powinno pokazać "Połączenie udane!"
4. Przejdź do zakładki "Wyszukiwanie NIP"
5. Wprowadź dowolny NIP (lub zostaw puste dla wszystkich faktur)
6. Wybierz folder do zapisu
7. Kliknij "Szukaj faktur"

**Oczekiwany rezultat:**
- W logach powinny pojawić się komunikaty typu:
  ```
  Znaleziono X folderów do przeszukania
  Przeszukiwanie folderu: INBOX
  Przeszukiwanie folderu: Test/Faktury
  Przeszukiwanie folderu: Test/Archiwum
  Przeszukiwanie folderu: Test/Podfolders/Deep
  ```
- Faktury z wszystkich folderów powinny zostać znalezione i zapisane

### Test 2: Wykrywanie faktur po wzorcu nazwy

**Cel:** Sprawdzenie czy aplikacja wykrywa faktury na podstawie wzorca w nazwie

**Kroki:**
1. Przygotuj testowe pliki PDF:
   - `faktura_123.pdf` - powinien zostać wykryty
   - `FAKTURA_VAT.pdf` - powinien zostać wykryty
   - `raport_miesięczny.pdf` - NIE powinien zostać wykryty
   - `fakt_2024.pdf` - powinien zostać wykryty
2. Wyślij te pliki jako załączniki do wiadomości email
3. Uruchom wyszukiwanie bez podawania NIP

**Oczekiwany rezultat:**
- Aplikacja powinna znaleźć tylko pliki zawierające "fakt" w nazwie
- `raport_miesięczny.pdf` powinien zostać pominięty
- Wielkość liter nie powinna mieć znaczenia

### Test 3: Zakładka "Znalezione"

**Cel:** Sprawdzenie funkcjonalności zakładki z listą znalezionych faktur

**Kroki:**
1. Po zakończeniu wyszukiwania przejdź do zakładki "Znalezione"
2. Sprawdź czy tabela zawiera kolumny: Data, Nadawca, Temat, Nazwa Pliku
3. Sprawdź czy dane są poprawne (zgodne ze znalezionymi fakturami)
4. Kliknij na nagłówek kolumny "Data" - tabela powinna się posortować
5. Kliknij ponownie - kolejność sortowania powinna się odwrócić
6. Posortuj po kolumnie "Nadawca"

**Oczekiwany rezultat:**
- Wszystkie znalezione faktury powinny być widoczne w tabeli
- Dane powinny być poprawne (data, nadawca, temat)
- Sortowanie powinno działać dla wszystkich kolumn

### Test 4: Otwieranie plików PDF

**Cel:** Sprawdzenie czy podwójne kliknięcie otwiera plik PDF

**Kroki:**
1. W zakładce "Znalezione" znajdź dowolną fakturę
2. Podwójnie kliknij na wiersz z fakturą

**Oczekiwany rezultat:**
- Plik PDF powinien otworzyć się w domyślnej aplikacji do przeglądania PDF
- Na Windows: użyje `startfile`
- Na macOS: użyje `open`
- Na Linux: użyje `xdg-open`

### Test 5: Obsługa brakujących plików

**Cel:** Sprawdzenie czy aplikacja radzi sobie z usuniętymi plikami

**Kroki:**
1. Po zakończeniu wyszukiwania ręcznie usuń jeden z zapisanych plików PDF
2. W zakładce "Znalezione" podwójnie kliknij na wiersz z usuniętym plikiem

**Oczekiwany rezultat:**
- Powinien pojawić się dialog informujący o braku pliku
- Dialog powinien oferować otwarcie folderu nadrzędnego
- Po kliknięciu "Tak" powinien otworzyć się folder

### Test 6: Polityka nadpisywania plików

**Cel:** Sprawdzenie polityki suffix (domyślnej)

**Kroki:**
1. Uruchom wyszukiwanie i zapisz faktury
2. Uruchom to samo wyszukiwanie ponownie (bez usuwania poprzednich plików)

**Oczekiwany rezultat:**
- Nowe pliki powinny otrzymać sufiks `_1`, `_2` itd.
- Przykład: `faktura.pdf`, `faktura_1.pdf`, `faktura_2.pdf`
- Stare pliki nie powinny zostać nadpisane

### Test 7: Trwałość danych "Znalezionych"

**Cel:** Sprawdzenie czy lista faktur jest zapisywana między sesjami

**Kroki:**
1. Uruchom wyszukiwanie i znajdź kilka faktur
2. Przejdź do zakładki "Znalezione" i sprawdź listę
3. Zamknij aplikację
4. Uruchom aplikację ponownie
5. Przejdź do zakładki "Znalezione"

**Oczekiwany rezultat:**
- Lista znalezionych faktur powinna być taka sama jak przed zamknięciem
- Dane powinny być wczytane z pliku `~/.poczta_faktury_found.json`

### Test 8: Czyszczenie listy "Znalezionych"

**Cel:** Sprawdzenie funkcji czyszczenia listy

**Kroki:**
1. W zakładce "Znalezione" kliknij przycisk "Wyczyść wszystko"
2. Potwierdź w dialogu

**Oczekiwany rezultat:**
- Tabela powinna być pusta
- Po ponownym uruchomieniu aplikacji lista powinna nadal być pusta

### Test 9: Przerwanie wyszukiwania

**Cel:** Sprawdzenie czy przycisk "Przerwij" działa podczas rekursywnego przeszukiwania

**Kroki:**
1. Uruchom wyszukiwanie na koncie z dużą liczbą folderów
2. Po rozpoczęciu przeszukiwania drugiego lub trzeciego folderu kliknij "Przerwij"

**Oczekiwany rezultat:**
- Wyszukiwanie powinno się zatrzymać
- Faktury znalezione do momentu przerwania powinny być zapisane
- Powinien pojawić się komunikat "Wyszukiwanie przerwane"

### Test 10: Konfiguracja zaawansowana

**Cel:** Sprawdzenie możliwości zmiany wzorca wykrywania faktur

**Kroki:**
1. Zamknij aplikację
2. Edytuj plik `~/.poczta_faktury_config.json`
3. Zmień `invoice_filename_pattern` na `"(fakt|invoice|rachunek)"`
4. Uruchom aplikację i wykonaj wyszukiwanie

**Oczekiwany rezultat:**
- Aplikacja powinna wykrywać pliki zawierające: "fakt", "invoice" lub "rachunek"
- Pliki z innymi nazwami powinny być pomijane

## Testy wydajnościowe

### Test 11: Duża liczba folderów

**Cel:** Sprawdzenie wydajności przy wielu folderach

**Kroki:**
1. Użyj konta z ponad 20 folderami
2. Uruchom przeszukiwanie

**Oczekiwany rezultat:**
- Aplikacja powinna pozostać responsywna
- GUI nie powinno się zawiesić
- Postęp powinien być widoczny w logach

### Test 12: Duża liczba wiadomości

**Cel:** Sprawdzenie wydajności przy wielu wiadomościach

**Kroki:**
1. Użyj konta z ponad 1000 wiadomości
2. Uruchom przeszukiwanie
3. Obserwuj użycie pamięci i CPU

**Oczekiwany rezultat:**
- Aplikacja nie powinna zużywać więcej niż 500 MB RAM
- CPU nie powinien być obciążone powyżej 50% (poza momentami przetwarzania PDF)

## Zgłaszanie błędów

Jeśli jakikolwiek test nie przeszedł pomyślnie, zgłoś błąd zawierający:
1. Numer testu i jego nazwę
2. Oczekiwany rezultat
3. Rzeczywisty rezultat
4. Pełny komunikat błędu (jeśli występuje)
5. Logi z aplikacji
6. Informacje o systemie (OS, wersja Python, wersja aplikacji)

## Czyszczenie po testach

Po zakończeniu testów:
1. Usuń pliki konfiguracyjne:
   - `~/.poczta_faktury_config.json`
   - `~/.poczta_faktury_found.json`
2. Usuń zapisane faktury testowe
3. Przywróć foldery email do stanu sprzed testów
