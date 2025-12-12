# Przykład użycia / Usage Example

## Szybki start / Quick Start

### 1. Instalacja / Installation

```bash
# Sklonuj repozytorium / Clone repository
git clone https://github.com/dzieju/Poczta-Faktury.git
cd Poczta-Faktury

# Zainstaluj zależności / Install dependencies
pip install -r requirements.txt
```

### 2. Uruchomienie / Running the Application

```bash
python main.py
```

### 3. Konfiguracja poczty / Email Configuration

#### Przykład dla Gmail:
- **Protokół**: IMAP
- **Serwer**: imap.gmail.com
- **Port**: 993
- **Email**: twoj.email@gmail.com
- **Hasło**: hasło aplikacji (wygenerowane w ustawieniach Google)
- **SSL**: ✓ (zaznaczone)

**Uwaga dla Gmail**: 
- Musisz utworzyć hasło aplikacji w ustawieniach konta Google
- Przejdź do: Konto Google → Bezpieczeństwo → Weryfikacja dwuetapowa → Hasła aplikacji

#### Przykład dla Outlook/Office365:
- **Protokół**: IMAP
- **Serwer**: outlook.office365.com
- **Port**: 993
- **Email**: twoj.email@outlook.com
- **Hasło**: twoje hasło
- **SSL**: ✓ (zaznaczone)

### 4. Wyszukiwanie faktur / Searching for Invoices

1. Przejdź do zakładki "Wyszukiwanie NIP"
2. Wprowadź numer NIP (np. 1234567890 lub 123-456-78-90)
3. Wybierz folder, w którym mają być zapisane znalezione faktury
4. Opcjonalnie wybierz zakres przeszukiwania (1/3/6 miesięcy) aby przeszukiwać tylko nowsze wiadomości
5. Opcjonalnie zaznacz "Zapisz ustawienia" aby pamiętać preferencje
6. Kliknij "Szukaj faktur"
7. Obserwuj postęp wyszukiwania w zakładce "Wyniki" wewnątrz "Wyszukiwanie NIP"
8. Znalezione pliki pojawiają się na żywo w zakładce "Znalezione" wewnątrz "Wyszukiwanie NIP"

**Uwaga o nowej strukturze**: Zakładka "Wyszukiwanie NIP" zawiera teraz dwie wewnętrzne zakładki:
- **Wyniki**: Pokazuje logi i postęp wyszukiwania
- **Znalezione**: Pokazuje listę znalezionych plików w czasie rzeczywistym podczas wyszukiwania

**Uwaga o zakresie przeszukiwania**: Jeśli zaznaczysz jedną lub więcej opcji zakresu czasowego (1 miesiąc, 3 miesiące, 6 miesięcy), aplikacja będzie filtrować i pomijać wiadomości starsze niż wybrany zakres. To przyspiesza wyszukiwanie w dużych skrzynkach pocztowych.

**Uwaga o konfiguracji**: Ustawienia mogą być zapisane w pliku `~/.poczta_faktury_config.json` i wczytywane przy następnym uruchomieniu aplikacji. Aby to włączyć, zaznacz checkbox "Zapisz ustawienia" w odpowiedniej zakładce.

### 5. Format NIP / NIP Format

Aplikacja rozpoznaje różne formaty NIP:
- Bez separatorów: `1234567890`
- Z kreskami: `123-456-78-90`
- Z kreskami (alternatywny format): `123-4567890`

### 6. Wyniki / Results

Aplikacja:
- Przeszuka wszystkie wiadomości email w skrzynce
- Pobierze załączniki PDF
- Przeskanuje je w poszukiwaniu podanego numeru NIP
- Zapisze znalezione faktury w wybranym folderze
- Wyświetla znalezione pliki **na żywo** w zakładce "Znalezione" w miarę ich wykrywania
- Po zakończeniu, wszystkie znalezione faktury są również dostępne w oddzielnej zakładce historii

Przykładowe nazwy zapisanych plików:
```
faktura_VAT_2024_01.pdf
faktura_proforma.pdf
paragon_fiskalny_1.pdf  (jeśli plik już istniał)
```

## Rozwiązywanie problemów / Troubleshooting

### Problem: "Nie można połączyć z serwerem"
- Sprawdź poprawność adresu serwera i portu
- Upewnij się, że masz połączenie z internetem
- Sprawdź czy firewall nie blokuje połączenia

### Problem: "Błąd logowania"
- Upewnij się, że hasło jest poprawne
- Dla Gmail użyj hasła aplikacji, nie głównego hasła
- Sprawdź czy konto nie wymaga dodatkowych kroków uwierzytelniania

### Problem: "Nie znaleziono faktur"
- Upewnij się, że numer NIP jest poprawny
- Sprawdź czy w skrzynce są wiadomości z załącznikami PDF
- Sprawdź czy pliki PDF zawierają frazę "fakt" w nazwie (domyślny wzorzec wykrywania)
- Pamiętaj, że aplikacja przeszukuje tylko załączniki w formacie PDF

## Nowe funkcje

### Zakładka "Znalezione"

Po wykonaniu wyszukiwania, wszystkie znalezione faktury są dostępne w zakładce "Znalezione":

1. **Przeglądanie listy**: Tabela zawiera dane, nadawcę, temat i nazwę pliku
2. **Sortowanie**: Kliknij na nagłówek kolumny aby posortować wyniki
3. **Otwieranie plików**: Podwójnie kliknij na wiersz aby otworzyć plik PDF
4. **Trwałość**: Lista jest zapisywana i dostępna po ponownym uruchomieniu aplikacji
5. **Czyszczenie**: Użyj przycisku "Wyczyść wszystko" aby usunąć wszystkie wpisy

### Rekursywne przeszukiwanie folderów

Aplikacja automatycznie przeszukuje **wszystkie foldery** w Twoim koncie email (IMAP):
- Nie musisz ręcznie przenosić wiadomości do INBOX
- Przeszukiwane są również podfoldery i zagnieżdżone struktury
- W logach zobaczysz nazwy przeszukiwanych folderów

### Zaawansowana konfiguracja

Możesz dostosować zachowanie aplikacji edytując plik `~/.poczta_faktury_config.json`:

```json
{
  "search_config": {
    "invoice_filename_pattern": "fakt",
    "overwrite_policy": "suffix",
    "search_all_folders": true
  }
}
```

**Parametry:**
- `invoice_filename_pattern`: Wzorzec (regex) do wykrywania faktur w nazwie pliku
  - Przykłady: `"fakt"`, `"(fakt|invoice)"`, `"(faktura|rachunek)"`
- `overwrite_policy`: Polityka nadpisywania plików
  - `"suffix"`: Dodaj sufiks `_1`, `_2` jeśli plik istnieje (domyślne)
  - `"overwrite"`: Nadpisz istniejący plik
- `search_all_folders`: Przeszukiwanie wszystkich folderów
  - `true`: Szukaj we wszystkich folderach (domyślne)
  - `false`: Szukaj tylko w INBOX

## Wskazówki / Tips

1. **Pierwsze użycie**: Zacznij od przetestowania połączenia w zakładce "Konfiguracja poczty"
2. **Duża skrzynka**: Jeśli masz dużo wiadomości, wyszukiwanie może zająć kilka minut
3. **Backup**: Zalecane jest regularne tworzenie kopii zapasowych znalezionych faktur
4. **Organizacja**: Twórz osobne foldery dla różnych kontrahentów/NIPów
5. **Zakładka Znalezione**: Użyj jej jako szybkiego dostępu do wszystkich znalezionych faktur
6. **Wzorzec wykrywania**: Dostosuj `invoice_filename_pattern` jeśli Twoje faktury mają inne nazwy
7. **Przerwanie**: Możesz w każdej chwili przerwać wyszukiwanie - znalezione do tej pory faktury zostaną zapisane

## Bezpieczeństwo / Security

- Aplikacja nie zapisuje danych logowania (chyba że zaznaczysz "Zapisz ustawienia")
- Hasła są przekazywane bezpośrednio do serwera email
- Używaj aplikacji tylko na zaufanych komputerach
- Regularnie zmieniaj hasła do poczty email
- Lista znalezionych faktur jest przechowywana lokalnie w `~/.poczta_faktury_found.json`
