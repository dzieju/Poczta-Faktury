# UI Changes: Date Picker Improvements

## Summary
This update improves the date range picker in the "Wyszukiwanie NIP" tab by removing quick select options and enhancing the calendar widget with Polish localization and month/year selection.

## Changes

### Before
The date picker UI had two sections:
1. **Zakres przeszukiwania** - A frame with 4 checkboxes for quick date selection:
   - "1 miesiąc" (1 month)
   - "3 miesiące" (3 months)
   - "6 miesięcy" (6 months)
   - "Ostatni tydzień" (Last week)

2. **Własny zakres dat (opcjonalnie)** - Custom date range with two DateEntry calendars
   - Limited functionality
   - Not localized (English interface)
   - No direct month/year selection

### After
The date picker now has a single, enhanced section:
1. **Zakres dat** - Simplified date range frame with:
   - Two DateEntry calendar widgets (From/To)
   - **Polish localization** (`locale='pl_PL'`)
   - **Month and year selection** enabled by default in the calendar dropdown
   - **No week numbers** (`showweeknumbers=False`)
   - Fallback support for systems without Polish locale

## User Experience Improvements

### 1. Cleaner Interface
- Removed 4 checkboxes that didn't work properly
- Single, unified date selection method
- Less visual clutter

### 2. Enhanced Calendar Widget
- **Month Selection**: Users can now click on the month name to select any month
- **Year Selection**: Users can now click on the year to select any year
- **Polish Interface**: All calendar text (months, days) in Polish
- **Direct Date Selection**: Click any date in the calendar to select it

### 3. More Flexible Date Range Selection
- Users can set any date range, not limited to predefined periods
- Both start and end dates can be set independently
- More intuitive for users who need specific date ranges

## Technical Details

### DateEntry Configuration
```python
DateEntry(
    date_range_frame, 
    width=12,
    background='darkblue',
    foreground='white',
    borderwidth=2,
    date_pattern='yyyy-mm-dd',
    locale='pl_PL',              # Polish localization
    showweeknumbers=False        # Hide week numbers
)
```

### Locale Fallback
The code includes error handling to fallback to the default locale if `pl_PL` is not available:
```python
try:
    # Try with Polish locale
    self.date_from_entry = DateEntry(..., locale='pl_PL', ...)
except Exception:
    # Fallback to default locale
    self.date_from_entry = DateEntry(..., showweeknumbers=False)
```

## Code Quality Improvements

### Removed Code
- Removed 4 boolean variables for quick select options
- Removed `_get_cutoff_datetime()` method (~20 lines)
- Removed quick select logic from configuration save/load
- Removed quick select logic from search methods

### Result
- **57 lines of code removed**
- Simplified logic
- Better maintainability
- No deprecated functionality

## Testing

### Validation
All changes were validated with automated tests:
- ✓ Quick select variables removed
- ✓ DateEntry configured with Polish locale
- ✓ DateEntry configured to hide week numbers
- ✓ `_get_cutoff_datetime` method removed
- ✓ Configuration handling updated
- ✓ No syntax errors
- ✓ No security vulnerabilities (CodeQL scan)

### Expected Behavior
1. User opens "Wyszukiwanie NIP" tab
2. Sees "Zakres dat" frame with two date pickers (Od/Do)
3. Clicks on "Od" date picker
4. Calendar opens in Polish with:
   - Polish month names (Styczeń, Luty, Marzec, etc.)
   - Polish day names (Pon, Wto, Śro, etc.)
   - Clickable month/year for selection
   - No week numbers displayed
5. User selects start date
6. Repeats for "Do" date picker
7. Clicks "Szukaj faktur" to search with the selected date range

## Compatibility

### Requirements
- Python 3.x
- tkcalendar >= 1.6.0
- tkinter (standard library)

### Locale Support
- **Best experience**: System with `pl_PL` locale installed
- **Fallback**: Works on any system, calendar will use default locale if Polish is not available

### Backward Compatibility
- Deprecated methods kept for programmatic usage
- Configuration file format unchanged (quick select fields simply ignored if present)
- Search functionality remains the same, only the UI changed

## Migration Notes

### For Users
- No action required
- Existing saved configurations will work (quick select settings are ignored)
- Users should use the calendar date pickers instead of remembering checkbox meanings

### For Developers
- `_get_cutoff_datetime()` method removed - use date picker values directly
- Quick select variables removed - update any code that referenced them
- Deprecated methods documented with replacement suggestions

## Future Enhancements

Potential future improvements:
1. Add preset buttons (e.g., "This Month", "Last Month") that set both date pickers
2. Add date range validation (highlight invalid ranges)
3. Add keyboard shortcuts for common date selections
4. Add date format preferences for different regions
