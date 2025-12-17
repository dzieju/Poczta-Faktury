"""
Rozszerzony prosty logger dla komponentów GUI z możliwością ustawienia poziomu logów
(i zapisu/odczytu poziomu z pliku konfiguracyjnego).
"""
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

# Domyślny plik konfiguracyjny (ten sam, którego używają inne moduły)
CONFIG_FILE = Path.home() / '.poczta_faktury_config.json'

# Mapowanie poziomów (zgodne ze standardem)
LOG_LEVELS = {
    'DEBUG': 10,
    'INFO': 20,
    'WARNING': 30,
    'ERROR': 40,
    'CRITICAL': 50
}

# Lista nazw poziomów (dla UI i walidacji)
LOG_LEVEL_NAMES = list(LOG_LEVELS.keys())

# Aktualny poziom (domyślnie INFO)
_current_level = LOG_LEVELS['INFO']


def _level_value(level_name: str) -> int:
    return LOG_LEVELS.get(level_name.upper(), LOG_LEVELS['INFO'])


def _validate_level(level_name: Optional[str]) -> Optional[str]:
    """
    Waliduje nazwę poziomu i zwraca znormalizowaną nazwę (uppercase) lub None jeśli nieprawidłowa.
    Obsługuje None i puste stringi.
    """
    if level_name and isinstance(level_name, str) and level_name.upper() in LOG_LEVELS:
        return level_name.upper()
    return None


def set_level(level_name: str):
    """
    Ustaw globalny poziom logów (np. 'DEBUG','INFO','WARNING','ERROR','CRITICAL').
    Wiadomości o poziomie mniejszym niż ustawiony będą pomijane.
    Poziom jest normalizowany do uppercase automatycznie.
    """
    global _current_level
    validated = _validate_level(level_name)
    if validated:
        _current_level = LOG_LEVELS[validated]
    else:
        _current_level = LOG_LEVELS['INFO']  # Fallback to INFO for invalid levels


def get_level() -> str:
    """Zwraca aktualny poziom logów jako nazwa (np. 'INFO')."""
    for name, val in LOG_LEVELS.items():
        if val == _current_level:
            return name
    return 'INFO'


def save_level_to_config(level_name: str, config_path: Optional[Path] = None):
    """
    Zapisz poziom logów do pliku konfiguracyjnego (klucz 'app' -> 'log_level').
    Tworzy plik jeśli nie istnieje. Zachowuje istniejące sekcje konfiguracji.
    """
    path = config_path or CONFIG_FILE
    cfg = {}
    try:
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
    except Exception:
        cfg = {}
    
    # Preserve all existing sections and only update app.log_level
    cfg.setdefault('app', {})
    cfg['app']['log_level'] = level_name
    
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        # Nie przerywamy działania aplikacji jeśli zapis się nie powiódł
        pass


def init_from_config(config_path: Optional[Path] = None):
    """
    Spróbuj wczytać poziom logów z pliku konfiguracyjnego i ustawić go.
    Oczekiwana struktura: { "app": { "log_level": "DEBUG" } }
    Waliduje poziom przed ustawieniem - nieprawidłowe wartości są ignorowane.
    """
    path = config_path or CONFIG_FILE
    try:
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
                lvl = cfg.get('app', {}).get('log_level')
                validated = _validate_level(lvl)
                if validated:
                    set_level(validated)
    except Exception:
        # Ignorujemy błędy czytania i pozostawiamy domyślny poziom
        pass


def log(message: str, level: str = "INFO"):
    """
    Drukuje wiadomość jeżeli poziom message >= aktualnego poziomu.
    Format: [YYYY-MM-DD HH:MM:SS] [LEVEL] message
    """
    try:
        lvl_val = _level_value(level)
        if lvl_val < _current_level:
            return
    except Exception:
        # Jeśli nieprawidłowy poziom, traktuj jako INFO
        if LOG_LEVELS['INFO'] < _current_level:
            return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level.upper()}] {message}", flush=True)
    sys.stdout.flush()
