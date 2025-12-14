#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for mail_accounts functionality
"""
import sys
import os
import tempfile
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from mail_accounts import MailAccountManager


def test_mail_accounts():
    """Test mail account manager functionality"""
    
    # Create a temporary config file
    temp_dir = tempfile.mkdtemp()
    test_config = os.path.join(temp_dir, "test_mail_config.json")
    
    print("=" * 60)
    print("Testing MailAccountManager")
    print("=" * 60)
    
    # Create manager
    print("\n1. Creating MailAccountManager...")
    manager = MailAccountManager(config_file=test_config)
    print(f"✓ Manager created, accounts: {len(manager.accounts)}")
    
    # Add Exchange account
    print("\n2. Adding Exchange account...")
    exchange_account = {
        "name": "Test Exchange",
        "type": "exchange",
        "email": "test@example.com",
        "username": "test@example.com",
        "password": "test_password",
        "exchange_server": "mail.example.com",
        "domain": "example.com"
    }
    idx = manager.add_account(exchange_account)
    print(f"✓ Exchange account added at index {idx}")
    
    # Add IMAP account
    print("\n3. Adding IMAP account...")
    imap_account = {
        "name": "Test IMAP",
        "type": "imap_smtp",
        "email": "imap@example.com",
        "username": "imap@example.com",
        "password": "imap_password",
        "imap_server": "imap.example.com",
        "imap_port": 993,
        "imap_ssl": True,
        "smtp_server": "smtp.example.com",
        "smtp_port": 587,
        "smtp_ssl": True
    }
    idx = manager.add_account(imap_account)
    print(f"✓ IMAP account added at index {idx}")
    
    # Add POP3 account
    print("\n4. Adding POP3 account...")
    pop3_account = {
        "name": "Test POP3",
        "type": "pop3_smtp",
        "email": "pop3@example.com",
        "username": "pop3@example.com",
        "password": "pop3_password",
        "pop3_server": "pop3.example.com",
        "pop3_port": 995,
        "pop3_ssl": True,
        "smtp_server_pop3": "smtp.example.com",
        "smtp_port_pop3": 587,
        "smtp_ssl_pop3": True
    }
    idx = manager.add_account(pop3_account)
    print(f"✓ POP3 account added at index {idx}")
    
    print(f"\nTotal accounts: {manager.get_account_count()}")
    
    # Test get_accounts_by_type
    print("\n5. Testing get_accounts_by_type...")
    exchange_accounts = manager.get_accounts_by_type("exchange")
    print(f"✓ Found {len(exchange_accounts)} Exchange account(s)")
    
    imap_accounts = manager.get_accounts_by_type("imap_smtp")
    print(f"✓ Found {len(imap_accounts)} IMAP account(s)")
    
    pop3_accounts = manager.get_accounts_by_type("pop3_smtp")
    print(f"✓ Found {len(pop3_accounts)} POP3 account(s)")
    
    # Save config
    print("\n6. Saving configuration...")
    if manager.save_config():
        print(f"✓ Configuration saved to {test_config}")
    else:
        print("✗ Failed to save configuration")
        return False
    
    # Load config in new manager
    print("\n7. Loading configuration in new manager...")
    manager2 = MailAccountManager(config_file=test_config)
    print(f"✓ Loaded {len(manager2.accounts)} accounts")
    
    # Verify accounts
    print("\n8. Verifying loaded accounts...")
    for i, account in enumerate(manager2.accounts):
        print(f"   Account {i}: {account['name']} ({account['type']})")
    
    # Get main account
    print("\n9. Getting main account...")
    main_account = manager2.get_main_account()
    if main_account:
        print(f"✓ Main account: {main_account['name']}")
    else:
        print("✗ No main account found")
        return False
    
    # Set a different main account
    print("\n10. Setting IMAP account as main...")
    if manager2.set_main_account(1):
        print("✓ Main account changed")
        main_account = manager2.get_main_account()
        print(f"   New main account: {main_account['name']}")
    else:
        print("✗ Failed to change main account")
        return False
    
    # Test credential validation
    print("\n11. Testing credential validation...")
    valid = manager2.validate_account_credentials(exchange_account)
    print(f"✓ Exchange credentials valid: {valid}")
    
    valid = manager2.validate_account_credentials(imap_account)
    print(f"✓ IMAP credentials valid: {valid}")
    
    valid = manager2.validate_account_credentials(pop3_account)
    print(f"✓ POP3 credentials valid: {valid}")
    
    # Test edit account
    print("\n12. Testing account edit...")
    edit_data = {"name": "Modified IMAP Account"}
    if manager2.edit_account(1, edit_data):
        print("✓ Account edited successfully")
        edited = manager2.get_account(1)
        print(f"   New name: {edited['name']}")
    else:
        print("✗ Failed to edit account")
        return False
    
    # Test remove account
    print("\n13. Testing account removal...")
    initial_count = manager2.get_account_count()
    if manager2.remove_account(2):  # Remove POP3 account
        print("✓ Account removed successfully")
        print(f"   Account count: {initial_count} -> {manager2.get_account_count()}")
    else:
        print("✗ Failed to remove account")
        return False
    
    # Cleanup
    os.remove(test_config)
    os.rmdir(temp_dir)
    
    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_mail_accounts()
    sys.exit(0 if success else 1)
