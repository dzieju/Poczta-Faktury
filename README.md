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
python poczta_faktury.py
```

2. W zakładce "Konfiguracja poczty":
   - Wybierz protokół (IMAP, POP3 lub Exchange)
   - Podaj adres serwera email (np. imap.gmail.com)
   - Podaj port (domyślnie 993 dla IMAP SSL)
   - Wprowadź adres email i hasło
   - Zaznacz "Użyj SSL/TLS" jeśli wymagane
   - Kliknij "Testuj połączenie" aby sprawdzić poprawność konfiguracji

3. W zakładce "Wyszukiwanie NIP":
   - Wprowadź numer NIP do wyszukania
   - Wybierz folder, w którym mają być zapisane znalezione faktury
   - Kliknij "Szukaj faktur"

4. Aplikacja przeszuka wszystkie załączniki PDF w skrzynce email i zapisze te, które zawierają podany numer NIP.

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
- ✅ Pasek postępu i informacje o przebiegu wyszukiwania
- ✅ Obsługa różnych formatów zapisu NIP (z kreskami i bez)

## Uwagi

- Aplikacja wymaga dostępu do internetu
- Wyszukiwanie dużej liczby wiadomości może zająć kilka minut
- Niektóre serwery email mogą wymagać specjalnych uprawnień lub haseł aplikacji
