#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testy dla EmailAccountManager
"""

import sys
import os
import tempfile
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import directly from file to avoid tkinter dependency
import importlib.util
spec = importlib.util.spec_from_file_location(
    "email_account_manager",
    os.path.join(os.path.dirname(__file__), '..', 'poczta_faktury', 'email_account_manager.py')
)
email_account_manager_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(email_account_manager_module)
EmailAccountManager = email_account_manager_module.EmailAccountManager


def test_create_empty_manager():
    """Test tworzenia pustego managera"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        config_file = Path(f.name)
    
    try:
        manager = EmailAccountManager(config_file)
        assert not manager.has_accounts()
        assert manager.get_active_account() is None
        assert len(manager.get_accounts()) == 0
    finally:
        if config_file.exists():
            config_file.unlink()


def test_add_account():
    """Test dodawania konta"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        config_file = Path(f.name)
    
    try:
        manager = EmailAccountManager(config_file)
        
        account = {
            'email': 'test@example.com',
            'name': 'Test Account',
            'protocol': 'IMAP',
            'server': 'imap.example.com',
            'port': '993',
            'password': 'secret',
            'use_ssl': True,
            'pdf_engine': 'pdfplumber'
        }
        
        result = manager.add_account(account)
        assert result
        assert manager.has_accounts()
        assert len(manager.get_accounts()) == 1
        
        # First account should be active
        active = manager.get_active_account()
        assert active is not None
        assert active['email'] == 'test@example.com'
        
    finally:
        if config_file.exists():
            config_file.unlink()


def test_add_duplicate_account():
    """Test dodawania duplikatu konta"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        config_file = Path(f.name)
    
    try:
        manager = EmailAccountManager(config_file)
        
        account = {
            'email': 'test@example.com',
            'name': 'Test Account',
        }
        
        result1 = manager.add_account(account)
        assert result1
        
        result2 = manager.add_account(account)
        assert not result2
        assert len(manager.get_accounts()) == 1
        
    finally:
        if config_file.exists():
            config_file.unlink()


def test_remove_account():
    """Test usuwania konta"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        config_file = Path(f.name)
    
    try:
        manager = EmailAccountManager(config_file)
        
        manager.add_account({'email': 'test1@example.com'})
        manager.add_account({'email': 'test2@example.com'})
        
        assert len(manager.get_accounts()) == 2
        
        result = manager.remove_account('test1@example.com')
        assert result
        assert len(manager.get_accounts()) == 1
        assert manager.get_account_by_email('test2@example.com') is not None
        
    finally:
        if config_file.exists():
            config_file.unlink()


def test_update_account():
    """Test aktualizacji konta"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        config_file = Path(f.name)
    
    try:
        manager = EmailAccountManager(config_file)
        
        manager.add_account({
            'email': 'test@example.com',
            'name': 'Old Name',
            'server': 'old.server.com'
        })
        
        result = manager.update_account('test@example.com', {
            'name': 'New Name',
            'server': 'new.server.com'
        })
        
        assert result
        
        account = manager.get_account_by_email('test@example.com')
        assert account['name'] == 'New Name'
        assert account['server'] == 'new.server.com'
        
    finally:
        if config_file.exists():
            config_file.unlink()


def test_set_active_account():
    """Test ustawiania aktywnego konta"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        config_file = Path(f.name)
    
    try:
        manager = EmailAccountManager(config_file)
        
        manager.add_account({'email': 'test1@example.com'})
        manager.add_account({'email': 'test2@example.com'})
        
        # First account should be active
        assert manager.get_active_account()['email'] == 'test1@example.com'
        
        # Change active account
        result = manager.set_active_account('test2@example.com')
        assert result
        assert manager.get_active_account()['email'] == 'test2@example.com'
        
    finally:
        if config_file.exists():
            config_file.unlink()


def test_persistence():
    """Test zapisywania i wczytywania z pliku"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        config_file = Path(f.name)
    
    try:
        # Create and populate manager
        manager1 = EmailAccountManager(config_file)
        manager1.add_account({'email': 'test1@example.com', 'name': 'Account 1'})
        manager1.add_account({'email': 'test2@example.com', 'name': 'Account 2'})
        manager1.set_active_account('test2@example.com')
        
        # Create new manager and load from file
        manager2 = EmailAccountManager(config_file)
        
        assert len(manager2.get_accounts()) == 2
        assert manager2.get_active_account()['email'] == 'test2@example.com'
        assert manager2.get_account_by_email('test1@example.com')['name'] == 'Account 1'
        
    finally:
        if config_file.exists():
            config_file.unlink()


def test_migration_from_old_format():
    """Test migracji ze starego formatu konfiguracji"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        config_file = Path(f.name)
    
    try:
        # Create old format config
        old_config = {
            'email_config': {
                'email': 'old@example.com',
                'protocol': 'IMAP',
                'server': 'imap.example.com',
                'port': '993',
                'password': 'secret',
                'use_ssl': True,
                'pdf_engine': 'pdfplumber'
            },
            'search_config': {
                'nip': '1234567890'
            }
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(old_config, f)
        
        # Load with manager - should migrate
        manager = EmailAccountManager(config_file)
        
        assert manager.has_accounts()
        assert len(manager.get_accounts()) == 1
        
        account = manager.get_active_account()
        assert account is not None
        assert account['email'] == 'old@example.com'
        assert account['server'] == 'imap.example.com'
        
        # Verify old format was removed
        with open(config_file, 'r', encoding='utf-8') as f:
            new_config = json.load(f)
        
        assert 'email_config' not in new_config
        assert 'accounts' in new_config
        assert 'active_account' in new_config
        assert 'search_config' in new_config  # Should be preserved
        
    finally:
        if config_file.exists():
            config_file.unlink()


if __name__ == '__main__':
    print("Running EmailAccountManager tests...")
    test_create_empty_manager()
    print("✓ test_create_empty_manager")
    
    test_add_account()
    print("✓ test_add_account")
    
    test_add_duplicate_account()
    print("✓ test_add_duplicate_account")
    
    test_remove_account()
    print("✓ test_remove_account")
    
    test_update_account()
    print("✓ test_update_account")
    
    test_set_active_account()
    print("✓ test_set_active_account")
    
    test_persistence()
    print("✓ test_persistence")
    
    test_migration_from_old_format()
    print("✓ test_migration_from_old_format")
    
    print("\nAll tests passed!")
