# Funkcja: Własny zakres dat w zakładce "Wyszukiwanie NIP"

## Przegląd

Aplikacja Poczta-Faktury została rozszerzona o funkcję precyzyjnego wyboru zakresu dat za pomocą kalendarzy "Od - Do" w zakładce "Wyszukiwanie NIP". Ta funkcja umożliwia dokładne określenie okresu, z którego mają być przeszukiwane wiadomości email.

## Lokalizacja

Funkcja znajduje się w zakładce **"Wyszukiwanie NIP"** w sekcji **"Własny zakres dat (opcjonalnie)"**, poniżej checkboxów z predefiniowanymi zakresami (1/3/6 miesięcy, ostatni tydzień).

## Komponenty UI

### 1. Kalendarz "Od" (Data początkowa)
- **Typ**: DateEntry (tkcalendar)
- **Format daty**: YYYY-MM-DD (ISO 8601)
- **Wartość domyślna**: Pusta (brak ograniczenia dolnego)
- **Funkcja**: Określa najwcześniejszą datę wiadomości do przeszukania (włącznie)

### 2. Kalendarz "Do" (Data końcowa)
- **Typ**: DateEntry (tkcalendar)
- **Format daty**: YYYY-MM-DD (ISO 8601)
- **Wartość domyślna**: Dzisiejsza data
- **Funkcja**: Określa najpóźniejszą datę wiadomości do przeszukania (włącznie)

### 3. Przycisk "Wyczyść zakres"
- **Funkcja**: Resetuje daty do wartości domyślnych
- **Efekt**: "Od" = puste, "Do" = dzisiaj

### 4. Etykieta informacyjna
- **Lokalizacja**: Obok przycisku "Wyczyść zakres"
- **Funkcja**: Wyświetla status po wyczyszczeniu zakresu

### 5. Wyświetlanie wybranego zakresu
- **Lokalizacja**: Nad paskiem postępu
- **Format**: "Wybrany zakres: Od YYYY-MM-DD Do YYYY-MM-DD"
- **Funkcja**: Potwierdza użytkownikowi wybrany zakres przed rozpoczęciem wyszukiwania

## Walidacja

### Reguły walidacji

1. **Data "Od" ≤ Data "Do"**
   - Warunek: Data początkowa nie może być późniejsza niż data końcowa
   - W przypadku naruszenia: Wyświetlany jest komunikat błędu "Data początkowa nie może być późniejsza niż data końcowa"
   - Wyszukiwanie jest blokowane do czasu poprawienia zakresu

2. **Opcjonalność dat**
   - Oba pola mogą być puste (przeszukiwane są wszystkie wiadomości)
   - Pole "Od" może być puste (przeszukiwanie od początku)
   - Pole "Do" może być puste (przeszukiwanie do końca)

3. **Format daty**
   - Kalendarz automatycznie zapewnia poprawny format YYYY-MM-DD
   - Niepoprawne daty są wykrywane przy próbie ich parsowania

## Logika filtrowania

### Priorytet zakresów

1. **Własny zakres dat (najwyższy priorytet)**
   - Jeśli wybrano "Od" lub "Do", ten zakres jest używany
   - Checkboxy (1/3/6 miesięcy) są ignorowane

2. **Predefiniowane zakresy (checkboxy)**
   - Używane tylko gdy własny zakres nie jest wybrany
   - Priorytet: 6m > 3m > 1m > 1 tydzień

3. **Brak zakresu**
   - Jeśli żaden zakres nie jest wybrany, przeszukiwane są wszystkie wiadomości

### Implementacja filtrowania

#### IMAP
- Używa natywnych kryteriów IMAP: `SINCE` i `BEFORE`
- Filtrowanie po stronie serwera (wydajne dla dużych skrzynek)
- Format daty IMAP: DD-MMM-YYYY (np. 01-Jun-2025)

**Przykład zapytania IMAP:**
```
SINCE 01-Jun-2025 BEFORE 01-Jul-2025
```

#### POP3
- Filtrowanie po stronie klienta (wszystkie wiadomości są pobierane)
- Parsowanie nagłówka `Date` każdej wiadomości
- Porównanie z zakresem [cutoff_dt, end_dt)

### Zakres dat - szczegóły techniczne

- **cutoff_dt**: Data początkowa (włącznie)
  - Konwersja: `datetime.combine(date_from, datetime.min.time())`
  - Wiadomości z datą >= cutoff_dt są uwzględniane

- **end_dt**: Data końcowa (wyłącznie)
  - Konwersja: `datetime.combine(date_to, datetime.min.time()) + timedelta(days=1)`
  - Wiadomości z datą < end_dt są uwzględniane
  - Dodanie 1 dnia zapewnia włączenie całego dnia końcowego

**Przykład:**
```python
# Użytkownik wybiera: Od 2025-06-01, Do 2025-06-30
cutoff_dt = datetime(2025, 6, 1, 0, 0, 0)   # Włącznie
end_dt = datetime(2025, 7, 1, 0, 0, 0)      # Wyłącznie

# Uwzględnione są wiadomości z zakresu [2025-06-01 00:00:00, 2025-07-01 00:00:00)
# Czyli wszystkie wiadomości z czerwca 2025
```

## Obsługa błędów

### Brak daty w wiadomości
- **Zachowanie**: Wiadomość nie jest odrzucana
- **Powód**: Niektóre wiadomości mogą nie mieć nagłówka `Date`
- **Polityka**: Lepiej uwzględnić wiadomość niż ją pominąć

### Nieprawidłowy format daty w wiadomości
- **Zachowanie**: Wiadomość nie jest odrzucana
- **Powód**: Parsowanie daty może się nie udać dla niestandardowych formatów
- **Polityka**: Błędy parsowania nie powinny blokować wyszukiwania

### Nieprawidłowy zakres wybrany przez użytkownika
- **Zachowanie**: Wyświetlany jest komunikat błędu
- **Wyszukiwanie**: Zablokowane do czasu poprawienia zakresu
- **Walidacja**: Wykonywana przed rozpoczęciem wyszukiwania

## Zapisywanie konfiguracji

### Pola zapisywane w pliku konfiguracyjnym

```json
{
  "search_config": {
    "date_from": "2025-06-01",  // ISO format YYYY-MM-DD lub null
    "date_to": "2025-06-30",    // ISO format YYYY-MM-DD lub null
    // ... inne pola
  }
}
```

### Warunki zapisywania

- Checkbox "Zapisz ustawienia" musi być zaznaczony
- Daty są zapisywane w formacie ISO (YYYY-MM-DD)
- `null` jest zapisywane gdy pole jest puste

### Przywracanie konfiguracji

- Przy starcie aplikacji daty są automatycznie przywracane
- Nieprawidłowe daty (błąd parsowania) są ignorowane
- Pola są resetowane do wartości domyślnych w przypadku błędu

## Przykłady użycia

### Przykład 1: Wyszukiwanie faktur z ostatniego miesiąca
```
Od: 2025-11-16
Do: 2025-12-16
```
**Efekt**: Przeszukiwane są tylko wiadomości z ostatnich 30 dni

### Przykład 2: Wyszukiwanie faktur z konkretnego kwartału
```
Od: 2025-01-01
Do: 2025-03-31
```
**Efekt**: Przeszukiwane są tylko wiadomości z Q1 2025

### Przykład 3: Wyszukiwanie wszystkich faktur do końca czerwca
```
Od: (puste)
Do: 2025-06-30
```
**Efekt**: Przeszukiwane są wszystkie wiadomości do 30 czerwca 2025 włącznie

### Przykład 4: Wyszukiwanie faktur od początku lipca do dziś
```
Od: 2025-07-01
Do: (dzisiejsza data)
```
**Efekt**: Przeszukiwane są wiadomości od 1 lipca do dzisiaj

## Kompatybilność wsteczna

### Istniejące funkcjonalności
- Checkboxy (1/3/6 miesięcy, ostatni tydzień) działają jak poprzednio
- Własny zakres ma priorytet, ale nie usuwa checkboxów
- Metoda `_get_cutoff_datetime()` jest nadal używana gdy własny zakres nie jest wybrany

### Brak tkcalendar
- Jeśli biblioteka tkcalendar nie jest zainstalowana, wyświetlany jest komunikat
- Aplikacja działa normalnie z użyciem checkboxów
- Funkcja jest opcjonalna i nie blokuje podstawowych możliwości

## API wewnętrzne

### Metody

#### `validate_date_range()`
```python
def validate_date_range(self) -> tuple[bool, date, date, str]:
    """
    Walidacja zakresu dat.
    
    Returns:
        tuple: (is_valid, date_from, date_to, error_message)
    """
```

#### `clear_date_range()`
```python
def clear_date_range(self):
    """Wyczyść wybrane daty w zakresie czasowym"""
```

#### `_email_date_is_within_range(date_header, cutoff_dt, end_dt)`
```python
def _email_date_is_within_range(self, date_header, cutoff_dt, end_dt=None) -> bool:
    """
    Sprawdza czy data wiadomości mieści się w zakresie [cutoff_dt, end_dt).
    
    Args:
        date_header: Email Date header string
        cutoff_dt: Start datetime (inclusive) or None
        end_dt: End datetime (exclusive) or None
        
    Returns:
        bool: True if email date is within range
    """
```

### Parametry wyszukiwania

```python
params = {
    'nip': str,
    'output_folder': str,
    'protocol': str,
    'cutoff_dt': datetime | None,  # Nowe
    'end_dt': datetime | None       # Nowe
}
```

## Testy

### Testy jednostkowe
Plik: `tests/test_date_range_picker.py`

**Przypadki testowe:**
1. Brak zakresu dat (None, None)
2. Poprawny zakres (Od < Do)
3. Niepoprawny zakres (Od > Do)
4. Tylko data "Od"
5. Tylko data "Do"
6. Email w zakresie
7. Email przed zakresem
8. Email po zakresie
9. Brak nagłówka Date w emailu
10. Nieprawidłowy nagłówek Date w emailu

### Weryfikacja logiki
Skrypt weryfikacyjny: `test_date_logic.py` (tymczasowy)

**Pokrycie:**
- Filtrowanie z różnymi kombinacjami dat
- Kalkulacja zakresu dat
- Włączność/wyłączność granic

## Zależności

### Nowe zależności
```
tkcalendar>=1.6.0
```

### Wymagania systemowe
- Python 3.7+
- tkinter (standardowa biblioteka)
- tkcalendar (zewnętrzna, opcjonalna)

## Znane ograniczenia

1. **Format daty**
   - Tylko ISO format (YYYY-MM-DD)
   - Brak możliwości zmiany formatu przez użytkownika

2. **Strefa czasowa**
   - Strefy czasowe są usuwane przy porównywaniu
   - Zakłada się lokalny czas serwera email

3. **Dokładność**
   - Precyzja do dnia (nie godziny)
   - Data końcowa jest włącznie (cały dzień)

4. **POP3**
   - Wszystkie wiadomości są pobierane przed filtrowaniem
   - Może być wolne dla dużych skrzynek

## Przyszłe usprawnienia

1. **Presety zakresów**
   - Przyciski "Ostatnie 7 dni", "Ostatni miesiąc" itp.
   - Szybkie ustawianie popularnych zakresów

2. **Wizualizacja zakresu**
   - Wykres słupkowy pokazujący liczbę wiadomości w czasie
   - Podgląd zakresu przed wyszukiwaniem

3. **Historia zakresów**
   - Zapamiętywanie ostatnio używanych zakresów
   - Szybki wybór z historii

4. **Eksport zakresów**
   - Zapisywanie zakresów jako szablony
   - Udostępnianie zakresów między użytkownikami

## Wsparcie techniczne

### Zgłaszanie błędów
- Repository: https://github.com/dzieju/Poczta-Faktury
- Issues: https://github.com/dzieju/Poczta-Faktury/issues

### Kontakt
- Email: grzegorz.ciekot@woox.pl
- Telefon: 512 623 706 lub 34 363 2868

## Changelog

### v1.x.x (2025-12-16)
- ✨ Dodano własny zakres dat z kalendarzami "Od - Do"
- ✨ Dodano walidację zakresu dat
- ✨ Dodano przycisk "Wyczyść zakres"
- ✨ Dodano wyświetlanie wybranego zakresu
- 🐛 Poprawiono logikę filtrowania dla IMAP i POP3
- 📝 Rozszerzona dokumentacja o sekcję własnego zakresu dat
- ✅ Dodano testy jednostkowe dla funkcjonalności dat
