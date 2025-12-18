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

### 3. Ustawienia / Settings

#### Przykład dla Gmail:
- **Protokół**: IMAP (zalecane) lub POP3
- **Serwer**: 
  - IMAP: imap.gmail.com
  - POP3: pop.gmail.com
- **Port**: 
  - IMAP: 993
  - POP3: 995
- **Email**: twoj.email@gmail.com
- **Hasło**: **hasło aplikacji** (NIE twoje zwykłe hasło Gmail!)
- **SSL**: ✓ (zaznaczone)

**WAŻNE - Konfiguracja hasła aplikacji dla Gmail:**

Gmail wymaga hasła aplikacji (App Password) do połączeń przez IMAP/POP3, jeśli masz włączoną weryfikację dwuetapową. Bez hasła aplikacji zobaczysz błąd typu: `[AUTH] Application-specific password required`.

**Krok po kroku - generowanie hasła aplikacji:**

1. **Włącz weryfikację dwuetapową** (jeśli jeszcze nie jest włączona):
   - Przejdź do https://myaccount.google.com/security
   - Znajdź sekcję "Jak logujesz się w Google"
   - Kliknij "Weryfikacja dwuetapowa" i postępuj zgodnie z instrukcjami

2. **Wygeneruj hasło aplikacji**:
   - Przejdź bezpośrednio do: https://myaccount.google.com/apppasswords
   - (lub: Konto Google → Bezpieczeństwo → Weryfikacja dwuetapowa → Hasła aplikacji)
   - Zaloguj się ponownie, jeśli zostaniesz o to poproszony
   
3. **Utwórz nowe hasło**:
   - W polu "Wybierz aplikację" wybierz: **Poczta**
   - W polu "Wybierz urządzenie" wybierz: **Komputer z systemem Windows** (lub inne)
   - Kliknij **Generuj**

4. **Skopiuj hasło**:
   - Google wyświetli 16-znakowe hasło (w formacie: xxxx xxxx xxxx xxxx)
   - **Skopiuj to hasło** (możesz usunąć spacje lub wpisać je ze spacjami)
   - Hasło pojawi się tylko raz - zapisz je w bezpiecznym miejscu!

5. **Użyj hasła w aplikacji**:
   - Wklej wygenerowane hasło aplikacji w pole "Hasło" w Poczta-Faktury
   - Kliknij "Testuj połączenie" aby sprawdzić poprawność konfiguracji

**Rozwiązywanie problemów:**
- Jeśli nie widzisz opcji "Hasła aplikacji", upewnij się że weryfikacja dwuetapowa jest włączona
- Jeśli nadal masz problemy, sprawdź czy Twoje konto nie ma dodatkowych ograniczeń bezpieczeństwa
- Możesz wygenerować wiele haseł aplikacji dla różnych urządzeń/aplikacji
- Możesz odwołać hasło aplikacji w dowolnym momencie w tych samych ustawieniach

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

1. **Pierwsze użycie**: Zacznij od przetestowania połączenia w zakładce "Ustawienia"
2. **Duża skrzynka**: Jeśli masz dużo wiadomości, wyszukiwanie może zająć kilka minut
3. **Backup**: Zalecane jest regularne tworzenie kopii zapasowych znalezionych faktur
4. **Organizacja**: Twórz osobne foldery dla różnych kontrahentów/NIPów

## Bezpieczeństwo / Security

- Aplikacja nie zapisuje danych logowania
- Hasła są przekazywane bezpośrednio do serwera email
- Używaj aplikacji tylko na zaufanych komputerach
- Regularnie zmieniaj hasła do poczty email
