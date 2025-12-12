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
   - Opcjonalnie wybierz zakres przeszukiwania (1 miesiąc, 3 miesiące, 6 miesięcy)
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
- ✅ Interfejs graficzny w języku polskim
- ✅ Nieblokujące wyszukiwanie - GUI pozostaje responsywne podczas operacji
- ✅ Przycisk "Przerwij" do zatrzymania wyszukiwania w dowolnym momencie
- ✅ Pasek postępu i informacje o przebiegu wyszukiwania w czasie rzeczywistym
- ✅ Obsługa różnych formatów zapisu NIP (z kreskami i bez)
- ✅ Możliwość zapisania ustawień do pliku konfiguracyjnego
- ✅ Filtrowanie wiadomości według zakresu czasowego (1/3/6 miesięcy)
- ✅ Przełączanie widoczności hasła
- ✅ Ustawianie daty modyfikacji plików zgodnie z datą otrzymania emaila

## Uwagi

- Aplikacja wymaga dostępu do internetu
- Wyszukiwanie dużej liczby wiadomości może zająć kilka minut
- Możesz użyć przycisku "Przerwij" aby zatrzymać wyszukiwanie w dowolnym momencie
- Niektóre serwery email mogą wymagać specjalnych uprawnień lub haseł aplikacji
- Daty modyfikacji zapisanych plików odpowiadają dacie otrzymania emaila (sprawdź z `ls -l --time-style=long-iso`)
