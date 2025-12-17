# Zarządzanie wieloma kontami email

## Opis

Aplikacja Poczta-Faktury teraz obsługuje zarządzanie wieloma kontami email. Możesz:
1. Dodawać wiele kont pocztowych
2. Przełączać się między kontami
3. Edytować i usuwać konta
4. Zapisywać ustawienia kont w pliku konfiguracyjnym
5. Używać tylko wybranego aktywnego konta do wyszukiwania faktur

## Architektura

### EmailAccountManager

Nowa klasa `EmailAccountManager` (w pliku `poczta_faktury/email_account_manager.py`) zarządza:
- Listą kont pocztowych
- Aktywnym kontem
- Zapisem/odczytem z pliku JSON
- Migracją ze starego formatu konfiguracji

### Format pliku konfiguracyjnego

Konta są zapisywane w pliku `~/.poczta_faktury_config.json` w następującym formacie:

```json
{
  "accounts": [
    {
      "email": "konto1@example.com",
      "name": "Konto robocze",
      "protocol": "IMAP",
      "server": "imap.example.com",
      "port": "993",
      "password": "hasło1",
      "use_ssl": true,
      "pdf_engine": "pdfplumber"
    },
    {
      "email": "konto2@example.com",
      "name": "Konto prywatne",
      "protocol": "POP3",
      "server": "pop.example2.com",
      "port": "995",
      "password": "hasło2",
      "use_ssl": true,
      "pdf_engine": "pdfminer.six"
    }
  ],
  "active_account": "konto1@example.com",
  "search_config": {
    "nip": "",
    "output_folder": "",
    "save_search_settings": false,
    "date_from": null,
    "date_to": null
  }
}
```

### Migracja ze starego formatu

Jeśli masz istniejący plik konfiguracyjny ze starym formatem (klucz `email_config`), aplikacja automatycznie:
1. Utworzy konto z tych danych
2. Ustawi je jako aktywne
3. Zapisze w nowym formacie
4. Usunie stary klucz `email_config`

## Użycie

### 1. Sekcja "Zarządzanie kontami email" w zakładce Ustawienia

Po uruchomieniu aplikacji przejdź do zakładki **Ustawienia**. Na dole znajdziesz nową sekcję:

#### Aktywne konto
- Rozwijana lista wszystkich kont
- Wybierz konto, które ma być używane do wyszukiwania
- Zmiana automatycznie ładuje dane konta do pól edycji

#### Lista kont
- Wyświetla wszystkie zapisane konta
- Format: `Nazwa konta (email@example.com)`
- Przewijana lista dla wielu kont

#### Przyciski zarządzania

**Dodaj konto**
- Otwiera dialog z polami:
  - Nazwa konta (opcjonalna)
  - Email (wymagany)
  - Protokół (IMAP/POP3/Exchange)
  - Serwer
  - Port
  - Hasło
  - SSL/TLS
  - Silnik PDF
- Po zapisaniu konto pojawia się na liście

**Edytuj konto**
- Wybierz konto z listy
- Kliknij "Edytuj konto"
- Zmień dowolne pola (oprócz emaila)
- Zapisz zmiany

**Usuń konto**
- Wybierz konto z listy
- Kliknij "Usuń konto"
- Potwierdź usunięcie
- Jeśli usunięto aktywne konto, automatycznie wybierane jest inne

**Załaduj do pól**
- Wybierz konto z listy
- Kliknij "Załaduj do pól"
- Dane konta wypełnią pola edycji u góry

### 2. Testowanie połączenia

Po wypełnieniu pól u góry zakładki:
1. Kliknij "Testuj połączenie"
2. Jeśli połączenie się powiedzie i zaznaczono "Zapisz ustawienia":
   - Konto zostanie dodane do listy (jeśli nowe)
   - Lub zaktualizowane (jeśli istnieje)
   - Automatycznie odświeży się lista kont

### 3. Wyszukiwanie faktur

W zakładce **Wyszukiwanie NIP**:
- Wyszukiwanie używa **tylko aktywnego konta**
- Przed rozpoczęciem wyszukiwania upewnij się, że odpowiednie konto jest aktywne
- Zmień aktywne konto w zakładce Ustawienia przed wyszukiwaniem

## Przykładowe scenariusze użycia

### Scenariusz 1: Pierwsze uruchomienie z istniejącą konfiguracją

1. Masz plik `~/.poczta_faktury_config.json` ze starym formatem
2. Uruchamiasz aplikację
3. Aplikacja automatycznie migruje konfigurację do nowego formatu
4. Twoje stare konto jest dostępne na liście i ustawione jako aktywne
5. Możesz teraz dodać więcej kont

### Scenariusz 2: Dodanie drugiego konta

1. Przejdź do zakładki Ustawienia
2. Kliknij "Dodaj konto"
3. Wypełnij dane drugiego konta
4. Kliknij "Zapisz"
5. Nowe konto pojawia się na liście
6. Możesz przełączyć się na nie wybierając z listy "Aktywne konto"

### Scenariusz 3: Przełączanie między kontami

1. Masz 3 konta: Praca, Dom, Dodatkowe
2. Aktualnie używasz konta "Praca"
3. Chcesz wyszukać faktury w koncie "Dom":
   - Przejdź do zakładki Ustawienia
   - Z listy "Aktywne konto" wybierz "dom@example.com"
   - Dane automatycznie załadują się do pól
   - Przejdź do zakładki Wyszukiwanie NIP
   - Rozpocznij wyszukiwanie - będzie używało konta "Dom"

### Scenariusz 4: Edycja hasła do konta

1. Zmieniłeś hasło do swojego konta email
2. Przejdź do zakładki Ustawienia
3. Wybierz konto z listy
4. Kliknij "Edytuj konto"
5. Zmień hasło
6. Kliknij "Zapisz"
7. Możesz przetestować połączenie klikając "Testuj połączenie"

### Scenariusz 5: Usunięcie nieużywanego konta

1. Masz stare konto, którego już nie używasz
2. Przejdź do zakładki Ustawienia
3. Wybierz konto z listy
4. Kliknij "Usuń konto"
5. Potwierdź usunięcie
6. Konto znika z listy

## Bezpieczeństwo

**UWAGA: Hasła są przechowywane w pliku konfiguracyjnym w postaci czystego tekstu.**

Zalecenia bezpieczeństwa:
1. Plik `~/.poczta_faktury_config.json` ma uprawnienia tylko dla Twojego użytkownika
2. Nie udostępniaj tego pliku
3. Rozważ użycie haseł aplikacji zamiast głównych haseł do kont (np. Gmail App Passwords)
4. Regularnie zmieniaj hasła
5. Jeśli komputer jest współdzielony, rozważ nie zapisywanie haseł

## API EmailAccountManager

Klasa `EmailAccountManager` oferuje następujące metody:

### Konstruktor
```python
manager = EmailAccountManager(config_file: Path)
```

### Metody

**add_account(account: Dict) -> bool**
- Dodaje nowe konto
- Zwraca True jeśli sukces, False jeśli konto już istnieje

**remove_account(email: str) -> bool**
- Usuwa konto po adresie email
- Zwraca True jeśli sukces, False jeśli konto nie istnieje

**update_account(email: str, updated_data: Dict) -> bool**
- Aktualizuje dane konta
- Zwraca True jeśli sukces, False jeśli konto nie istnieje

**get_accounts() -> List[Dict]**
- Zwraca listę wszystkich kont

**get_account_by_email(email: str) -> Optional[Dict]**
- Zwraca konto po adresie email lub None

**set_active_account(email: str) -> bool**
- Ustawia aktywne konto
- Zwraca True jeśli sukces, False jeśli konto nie istnieje

**get_active_account() -> Optional[Dict]**
- Zwraca aktywne konto lub None

**has_accounts() -> bool**
- Sprawdza czy są jakieś konta

## Testy

Testy jednostkowe znajdują się w pliku `tests/test_email_account_manager.py`:

```bash
python tests/test_email_account_manager.py
```

Testy obejmują:
- Tworzenie pustego managera
- Dodawanie kont
- Sprawdzanie duplikatów
- Usuwanie kont
- Aktualizację kont
- Ustawianie aktywnego konta
- Persystencję (zapis/odczyt z pliku)
- Migrację ze starego formatu

## Kompatybilność wsteczna

Aplikacja zachowuje pełną kompatybilność wsteczną:
1. Stare pliki konfiguracyjne są automatycznie migrowane
2. Zachowane są wszystkie ustawienia wyszukiwania
3. Istniejące funkcje działają tak samo
4. Można nadal używać aplikacji z jednym kontem

## Znane ograniczenia

1. Hasła są przechowywane w pliku w postaci czystego tekstu
2. Nie ma szyfrowania danych konfiguracyjnych
3. Nie ma synchronizacji między urządzeniami
4. Maksymalna liczba kont nie jest ograniczona, ale duża liczba (>20) może spowolnić interfejs

## Przyszłe usprawnienia

Planowane funkcje:
1. Szyfrowanie haseł w pliku konfiguracyjnym
2. Import/eksport kont
3. Grupowanie kont (np. praca, dom)
4. Kolorowe oznaczenia kont
5. Statystyki użycia kont
6. Automatyczne wykrywanie serwerów po adresie email
7. Obsługa OAuth2 dla Gmail/Outlook
