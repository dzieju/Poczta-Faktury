# UI Mockup: Custom Date Range Picker

## Visual Layout

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    Poczta Faktury - Wyszukiwanie faktur po NIP               ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║  [Ustawienia]  [Wyszukiwanie NIP]  [O programie]                            ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║  Numer NIP:      [____________________________________]                      ║
║                                                                               ║
║  Folder zapisu:  [____________________________] [Przeglądaj...]             ║
║                                                                               ║
║  ┌─ Zakres przeszukiwania ──────────────────────────────────────────────┐  ║
║  │  ☐ 1 miesiąc    ☐ 3 miesiące    ☐ 6 miesięcy    ☐ Ostatni tydzień   │  ║
║  └────────────────────────────────────────────────────────────────────────┘  ║
║                                                                               ║
║  ┌─ Własny zakres dat (opcjonalnie) ────────────────────────────────────┐  ║
║  │                                                                         │  ║
║  │  Od: [2025-01-01 ▼]  Do: [2025-12-31 ▼]  [Wyczyść zakres]           │  ║
║  │                                                                         │  ║
║  └────────────────────────────────────────────────────────────────────────┘  ║
║                                                                               ║
║  ☐ Zapisz ustawienia                                                         ║
║                                                                               ║
║  [Szukaj faktur] [Przerwij] [Znalezione ➜]                                  ║
║                                                                               ║
║  Wybrany zakres: Od 2025-01-01 Do 2025-12-31                                ║
║                                                                               ║
║  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  (Progress Bar)       ║
║                                                                               ║
║  Wyniki:                                                                     ║
║  ┌───────────────────────────────────────────────────────────────────────┐  ║
║  │ Rozpoczynam wyszukiwanie...                                           │  ║
║  │ Przeszukuję wiadomości od: 2025-01-01 do: 2025-12-31                │  ║
║  │ Połączono z serwerem IMAP                                            │  ║
║  │ Używam filtrowania IMAP: SINCE 01-Jan-2025 BEFORE 01-Jan-2026       │  ║
║  │ Znaleziono 50 wiadomości do przeszukania                            │  ║
║  │ Przetworzono 10/50 wiadomości...                                     │  ║
║  │ ✓ Znaleziono: faktura_01.pdf (z: Re: Faktury za styczeń)           │  ║
║  │ ✓ Znaleziono: FV_2025_001.pdf (z: Faktura VAT 001/2025)            │  ║
║  │                                                                       │  ║
║  │                                                                       │  ║
║  └───────────────────────────────────────────────────────────────────────┘  ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

## Calendar Widget Popup

When clicking on "Od" or "Do" field:

```
┌─────────────────────────┐
│  ◀  Grudzień 2025   ▶   │
├─────────────────────────┤
│ Po Wt Śr Cz Pt So Ni   │
├─────────────────────────┤
│  1  2  3  4  5  6  7   │
│  8  9 10 11 12 13 14   │
│ 15 [16]17 18 19 20 21   │  ← Selected: 16
│ 22 23 24 25 26 27 28   │
│ 29 30 31               │
└─────────────────────────┘
```

## Validation Error Display

When Od > Do:

```
┌─────────────────────────────────────────────────┐
│  ⚠️  Błąd zakresu dat                           │
├─────────────────────────────────────────────────┤
│                                                  │
│  Data początkowa nie może być późniejsza niż    │
│  data końcowa                                    │
│                                                  │
│  [OK]                                           │
└─────────────────────────────────────────────────┘
```

## States and Interactions

### Default State (No Custom Range)
```
Od: [____________ ▼]  Do: [2025-12-16 ▼]  [Wyczyść zakres]
```
- "Od" field is empty
- "Do" field shows today's date
- Checkboxes can be used for predefined ranges

### Custom Range Selected
```
Od: [2025-01-01 ▼]  Do: [2025-12-31 ▼]  [Wyczyść zakres]

Wybrany zakres: Od 2025-01-01 Do 2025-12-31
```
- Both fields show selected dates
- Selected range is displayed in green bold text
- Checkboxes are ignored

### Only "Od" Selected
```
Od: [2025-06-01 ▼]  Do: [____________ ▼]  [Wyczyść zakres]

Wybrany zakres: Od 2025-06-01
```
- Only start date is shown
- Searches from start date to present

### Only "Do" Selected
```
Od: [____________ ▼]  Do: [2025-06-30 ▼]  [Wyczyść zakres]

Wybrany zakres: Do 2025-06-30
```
- Only end date is shown
- Searches from beginning to end date

### After Clicking "Wyczyść zakres"
```
Od: [____________ ▼]  Do: [2025-12-16 ▼]  [Wyczyść zakres]
                                            Zakres wyczyszczony
```
- "Od" is cleared
- "Do" is reset to today
- Info message appears briefly

## Color Scheme

- **Normal text**: Black on light gray background
- **Selected range label**: Green (#008000) bold
- **Error messages**: Red (#FF0000)
- **Calendar selected date**: Dark blue background, white text
- **Calendar today**: Light blue border
- **Info messages**: Blue (#0000FF)

## Responsive Behavior

### Window Resizing
- Date pickers maintain fixed width (150px each)
- Clear button maintains fixed width (120px)
- Info label expands to fill available space
- Results text area expands vertically

### Focus States
- Calendar widget: Blue border (2px)
- Clear button: Light gray background on hover
- Selected date in calendar: Blue highlight

## Accessibility

- **Tab order**: NIP → Folder → Checkboxes → Od → Do → Clear → Save → Search
- **Keyboard shortcuts**:
  - Enter in date field: Open calendar
  - Escape in calendar: Close calendar
  - Arrow keys in calendar: Navigate dates
  - Space on Clear button: Clear dates
  
## User Flow Diagram

```
Start
  │
  ├─→ User enters NIP
  │
  ├─→ User selects folder
  │
  ├─→ User chooses date range:
  │   ├─ Option A: Use checkboxes (existing behavior)
  │   └─ Option B: Use custom date range
  │       ├─→ Click "Od" field → Select date from calendar
  │       ├─→ Click "Do" field → Select date from calendar
  │       └─→ Validation: Od ≤ Do?
  │           ├─ Yes → Show "Wybrany zakres: ..."
  │           └─ No  → Show error dialog
  │
  ├─→ (Optional) Click "Wyczyść zakres" → Dates reset
  │
  └─→ Click "Szukaj faktur"
      └─→ Search begins with selected range
```

## Edge Cases - UI Behavior

### Case 1: Invalid Date Entry
```
Od: [2025-99-99 ▼]  Do: [2025-12-31 ▼]

[Error popup]: Nieprawidłowa data 'Od': 2025-99-99
```

### Case 2: tkcalendar Not Available
```
┌─ Własny zakres dat (opcjonalnie) ────────────────────────────────────┐
│  ⚠️ Kalendarz niedostępny - zainstaluj tkcalendar                    │
└────────────────────────────────────────────────────────────────────────┘
```

### Case 3: Both Custom Range and Checkbox Selected
```
☑ 3 miesiące

Od: [2025-01-01 ▼]  Do: [2025-12-31 ▼]

→ Custom range takes precedence
→ Checkbox is visually checked but functionally ignored
```

## Search Results - With Date Range

```
Wyniki:
┌───────────────────────────────────────────────────────────────────────┐
│ Rozpoczynam wyszukiwanie...                                           │
│ Przeszukuję wiadomości od: 2025-01-01 do: 2025-12-31                │
│ Połączono z serwerem IMAP                                            │
│ Używam filtrowania IMAP: SINCE 01-Jan-2025 BEFORE 01-Jan-2026       │
│ Znaleziono 120 wiadomości do przeszukania                           │
│ Przetworzono 20/120 wiadomości...                                    │
│ ✓ Znaleziono: faktura_01.pdf (z: Re: Faktury za styczeń)           │
│ ✓ Znaleziono: FV_2025_001.pdf (z: Faktura VAT 001/2025)            │
│ ✓ Znaleziono: FV_2025_002.pdf (z: Faktura VAT 002/2025)            │
│ Przetworzono 40/120 wiadomości...                                    │
│ ...                                                                   │
│                                                                       │
│ === Zakończono wyszukiwanie ===                                      │
│ Znaleziono faktur z NIP 1234567890: 5                               │
└───────────────────────────────────────────────────────────────────────┘
```

## Dimensions

- **Date picker width**: 150px
- **Clear button width**: 120px
- **Info label**: Flexible, expands to fill
- **Frame padding**: 10px
- **Label-to-widget spacing**: 5px
- **Widget vertical spacing**: 5px
- **Section vertical spacing**: 10px

## Font Specifications

- **Labels**: Arial, 9pt, regular
- **Input fields**: Arial, 9pt, regular
- **Selected range**: Arial, 9pt, bold
- **Error messages**: Arial, 9pt, bold
- **Results text**: Courier New, 8pt, regular

## Animation/Transitions

- **Calendar popup**: Instant (no fade)
- **Clear button hover**: Instant color change
- **Selected range label**: Instant update
- **Info message**: Appears instantly, stays for 2 seconds, fades out over 0.5s

## Notes

This mockup represents the visual design and interactions of the custom date range picker feature. The actual implementation uses tkinter and tkcalendar widgets with standard system styling, which may vary slightly based on the operating system.
