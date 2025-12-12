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

2. W zakładce "Konfiguracja poczty":
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
   - Opcjonalnie wybierz zakres przeszukiwania (1 miesiąc, 3 miesiące, 6 miesięcy lub ostatni tydzień)
   - Opcjonalnie zaznacz "Zapisz ustawienia" aby zapisać preferencje
   - Kliknij "Szukaj faktur"
   - Podczas wyszukiwania możesz kliknąć "Przerwij" aby zatrzymać operację

4. Aplikacja przeszuka wszystkie załączniki PDF w skrzynce email i zapisze te, które zawierają podany numer NIP.
   - Wyszukiwanie działa w tle - GUI pozostaje responsywne
   - Logi i postęp są wyświetlane w czasie rzeczywistym
   - Zapisane pliki mają datę modyfikacji ustawioną zgodnie z datą otrzymania emaila

**Uwaga**: Ustawienia aplikacji są zapisywane w pliku `~/.poczta_faktury_config.json` (jeśli zaznaczono opcję "Zapisz ustawienia"). Hasło do poczty jest zapisywane tylko gdy zaznaczysz checkbox "Zapisz ustawienia" w zakładce "Konfiguracja poczty".

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
- ✅ **NOWOŚĆ: Rekursywne przeszukiwanie wszystkich folderów i podfolderów** konta pocztowego
- ✅ **NOWOŚĆ: Zakładka "Znalezione"** wyświetlająca wszystkie znalezione faktury z możliwością otwierania plików
- ✅ **NOWOŚĆ: Wykrywanie faktur na podstawie wzorca nazwy pliku** (domyślnie: "fakt")
- ✅ **NOWOŚĆ: Konfiguracja polityki nadpisywania plików** (nadpisuj lub dodaj sufiks)
- ✅ Interfejs graficzny w języku polskim
- ✅ Nieblokujące wyszukiwanie - GUI pozostaje responsywne podczas operacji
- ✅ Przycisk "Przerwij" do zatrzymania wyszukiwania w dowolnym momencie
- ✅ Pasek postępu i informacje o przebiegu wyszukiwania w czasie rzeczywistym
- ✅ Obsługa różnych formatów zapisu NIP (z kreskami i bez)
- ✅ Możliwość zapisania ustawień do pliku konfiguracyjnego
- ✅ Filtrowanie wiadomości według zakresu czasowego (1/3/6 miesięcy lub ostatni tydzień)
- ✅ Przełączanie widoczności hasła
- ✅ Ustawianie daty modyfikacji plików zgodnie z datą otrzymania emaila
- ✅ Zakładka "O programie" z danymi kontaktowymi i wersją aplikacji
- ✅ Automatyczne wersjonowanie aplikacji (patch version zwiększana przy każdym push do main)

## Nowe funkcje - szczegóły

### Rekursywne przeszukiwanie folderów

Aplikacja automatycznie przeszukuje **wszystkie foldery i podfoldery** konta pocztowego (IMAP), nie tylko INBOX. Obejmuje to:
- Foldery główne (INBOX, Sent, Drafts, itp.)
- Podfoldery utworzone przez użytkownika
- Zagnieżdżone struktury folderów

### Zakładka "Znalezione"

Nowa zakładka wyświetla tabelę wszystkich znalezionych faktur z następującymi kolumnami:
- **Data** - data otrzymania emaila
- **Nadawca** - adres email nadawcy
- **Temat** - temat wiadomości
- **Nazwa Pliku** - nazwa zapisanego pliku PDF

Funkcje zakładki:
- **Sortowanie** - kliknij na nagłówek kolumny aby posortować dane
- **Otwieranie plików** - podwójne kliknięcie otwiera plik PDF w domyślnej aplikacji
- **Obsługa błędów** - jeśli plik nie istnieje, aplikacja oferuje otwarcie folderu nadrzędnego
- **Trwałość danych** - lista faktur jest zapisywana i wczytywana przy każdym uruchomieniu

### Wykrywanie faktur

Aplikacja wykrywa faktury na podstawie:
1. **Rozszerzenia pliku** - musi być `.pdf`
2. **Wzorca w nazwie** - domyślnie nazwa musi zawierać "fakt" (np. "faktura", "Faktura VAT", "fakt_123")
3. **Zawartości NIP** - (jeśli włączone wyszukiwanie po NIP)

Wzorzec można skonfigurować w pliku `~/.poczta_faktury_config.json`:
```json
{
  "search_config": {
    "invoice_filename_pattern": "fakt",  // lub regex: "(fakt|invoice|rachunek)"
    "overwrite_policy": "suffix",        // lub "overwrite"
    "search_all_folders": true
  }
}
```

## Uwagi

- Aplikacja wymaga dostępu do internetu
- Wyszukiwanie dużej liczby wiadomości może zająć kilka minut
- Możesz użyć przycisku "Przerwij" aby zatrzymać wyszukiwanie w dowolnym momencie
- Niektóre serwery email mogą wymagać specjalnych uprawnień lub haseł aplikacji
- Daty modyfikacji zapisanych plików odpowiadają dacie otrzymania emaila (sprawdź z `ls -l --time-style=long-iso`)
