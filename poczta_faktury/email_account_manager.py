#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Menedżer kont pocztowych - zarządzanie wieloma kontami email
"""

import json
from pathlib import Path
from typing import List, Dict, Optional


class EmailAccountManager:
    """Zarządza wieloma kontami email i ich konfiguracją"""
    
    def __init__(self, config_file: Path):
        """
        Inicjalizacja menedżera kont
        
        Args:
            config_file: Ścieżka do pliku konfiguracyjnego JSON
        """
        self.config_file = config_file
        self.accounts: List[Dict] = []
        self.active_account_email: Optional[str] = None
        self._load()
    
    def _load(self):
        """Wczytaj konta z pliku konfiguracyjnego"""
        if not self.config_file.exists():
            return
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Load accounts from new format
            if 'accounts' in config:
                self.accounts = config['accounts']
                self.active_account_email = config.get('active_account')
            # Migrate from old single-account format
            elif 'email_config' in config:
                self._migrate_from_old_format(config)
            
        except Exception as e:
            print(f"Błąd wczytywania kont: {e}")
    
    def _migrate_from_old_format(self, old_config: Dict):
        """
        Migruj ze starego formatu single-account do nowego formatu multi-account
        
        Args:
            old_config: Stara konfiguracja z kluczem 'email_config'
        """
        email_config = old_config.get('email_config', {})
        if email_config.get('email'):
            # Create account from old config
            account = {
                'email': email_config['email'],
                'name': email_config.get('name', email_config.get('email', 'Konto główne')),
                'protocol': email_config.get('protocol', 'IMAP'),
                'server': email_config.get('server', ''),
                'port': email_config.get('port', '993'),
                'password': email_config.get('password', ''),
                'use_ssl': email_config.get('use_ssl', True),
                'pdf_engine': email_config.get('pdf_engine', 'pdfplumber')
            }
            self.accounts = [account]
            self.active_account_email = account['email']
            # Save in new format
            self._save()
    
    def _save(self):
        """Zapisz konta do pliku konfiguracyjnego"""
        # Load existing config to preserve other settings
        existing_config = {}
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    existing_config = json.load(f)
        except Exception:
            existing_config = {}
        
        # Update accounts section
        existing_config['accounts'] = self.accounts
        existing_config['active_account'] = self.active_account_email
        
        # Remove old email_config if present (migration complete)
        if 'email_config' in existing_config:
            del existing_config['email_config']
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(existing_config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Błąd zapisu kont: {e}")
            raise
    
    def add_account(self, account: Dict) -> bool:
        """
        Dodaj nowe konto
        
        Args:
            account: Słownik z danymi konta (email, name, protocol, server, port, password, use_ssl, pdf_engine)
        
        Returns:
            True jeśli dodano, False jeśli konto o tym email już istnieje
        """
        email = account.get('email')
        if not email:
            raise ValueError("Konto musi mieć adres email")
        
        # Check if account already exists
        if self.get_account_by_email(email):
            return False
        
        # Add default values
        account.setdefault('name', email)
        account.setdefault('protocol', 'IMAP')
        account.setdefault('server', '')
        account.setdefault('port', '993')
        account.setdefault('password', '')
        account.setdefault('use_ssl', True)
        account.setdefault('pdf_engine', 'pdfplumber')
        
        self.accounts.append(account)
        
        # Set as active if it's the first account
        if len(self.accounts) == 1:
            self.active_account_email = email
        
        self._save()
        return True
    
    def remove_account(self, email: str) -> bool:
        """
        Usuń konto po adresie email
        
        Args:
            email: Adres email konta do usunięcia
        
        Returns:
            True jeśli usunięto, False jeśli konto nie istnieje
        """
        # Find the actual account in the list (not a copy)
        account = None
        for acc in self.accounts:
            if acc.get('email') == email:
                account = acc
                break
        
        if not account:
            return False
        
        self.accounts.remove(account)
        
        # If removed account was active, set new active account
        if self.active_account_email == email:
            self.active_account_email = self.accounts[0]['email'] if self.accounts else None
        
        self._save()
        return True
    
    def update_account(self, email: str, updated_data: Dict) -> bool:
        """
        Zaktualizuj dane konta
        
        Args:
            email: Adres email konta do aktualizacji
            updated_data: Nowe dane konta
        
        Returns:
            True jeśli zaktualizowano, False jeśli konto nie istnieje
        """
        # Find the actual account in the list (not a copy)
        account = None
        for acc in self.accounts:
            if acc.get('email') == email:
                account = acc
                break
        
        if not account:
            return False
        
        # Don't allow changing email address
        if 'email' in updated_data and updated_data['email'] != email:
            raise ValueError("Nie można zmienić adresu email konta")
        
        # Update account data
        account.update(updated_data)
        self._save()
        return True
    
    def get_accounts(self) -> List[Dict]:
        """
        Pobierz listę wszystkich kont
        
        Returns:
            Lista słowników z danymi kont
        """
        return self.accounts.copy()
    
    def get_account_by_email(self, email: str) -> Optional[Dict]:
        """
        Pobierz konto po adresie email
        
        Args:
            email: Adres email konta
        
        Returns:
            Słownik z danymi konta lub None jeśli nie znaleziono
        """
        for account in self.accounts:
            if account.get('email') == email:
                return account.copy()
        return None
    
    def set_active_account(self, email: str) -> bool:
        """
        Ustaw aktywne konto
        
        Args:
            email: Adres email konta do aktywacji
        
        Returns:
            True jeśli ustawiono, False jeśli konto nie istnieje
        """
        account = self.get_account_by_email(email)
        if not account:
            return False
        
        self.active_account_email = email
        self._save()
        return True
    
    def get_active_account(self) -> Optional[Dict]:
        """
        Pobierz aktywne konto
        
        Returns:
            Słownik z danymi aktywnego konta lub None jeśli nie ustawiono
        """
        if not self.active_account_email:
            return None
        return self.get_account_by_email(self.active_account_email)
    
    def has_accounts(self) -> bool:
        """
        Sprawdź czy są jakieś konta
        
        Returns:
            True jeśli są konta, False w przeciwnym razie
        """
        return len(self.accounts) > 0
