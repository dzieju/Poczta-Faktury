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
- Zapisze znalezione faktury w wybranym folderze z prefiksem numeru porządkowego

Przykładowe nazwy zapisanych plików:
```
1_faktura_VAT_2024_01.pdf
2_faktura_proforma.pdf
3_paragon_fiskalny.pdf
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
- Pamiętaj, że aplikacja przeszukuje tylko załączniki w formacie PDF

## Wskazówki / Tips

1. **Pierwsze użycie**: Zacznij od przetestowania połączenia w zakładce "Konfiguracja poczty"
2. **Duża skrzynka**: Jeśli masz dużo wiadomości, wyszukiwanie może zająć kilka minut
3. **Backup**: Zalecane jest regularne tworzenie kopii zapasowych znalezionych faktur
4. **Organizacja**: Twórz osobne foldery dla różnych kontrahentów/NIPów

## Bezpieczeństwo / Security

- Aplikacja nie zapisuje danych logowania
- Hasła są przekazywane bezpośrednio do serwera email
- Używaj aplikacji tylko na zaufanych komputerach
- Regularnie zmieniaj hasła do poczty email
