#!/usr/bin/env python3
"""
Tests for version_info module
"""

import os
import pytest
from version_info import get_pr_number, get_version_string


def test_get_version_string_basic():
    """Test that get_version_string returns a valid version string"""
    version_str = get_version_string()
    assert version_str.startswith("ver. ")
    # Should contain version from version.txt (1.0.20) or 'dev'
    assert "1.0.20" in version_str or "dev" in version_str


def test_get_pr_number_from_env():
    """Test PR number detection from environment variable"""
    # Save original env
    original_pr = os.environ.get('COPILOT_AGENT_PR_NUMBER')
    
    try:
        # Test with PR number set
        os.environ['COPILOT_AGENT_PR_NUMBER'] = '123'
        pr = get_pr_number()
        assert pr == '123'
        
        # Clean up and test without PR number
        del os.environ['COPILOT_AGENT_PR_NUMBER']
        pr = get_pr_number()
        # PR might be None or detected from git, just check it's a valid type
        assert pr is None or isinstance(pr, str)
        
    finally:
        # Restore original env
        if original_pr:
            os.environ['COPILOT_AGENT_PR_NUMBER'] = original_pr
        elif 'COPILOT_AGENT_PR_NUMBER' in os.environ:
            del os.environ['COPILOT_AGENT_PR_NUMBER']


def test_get_version_string_with_pr():
    """Test that version string includes PR number when available"""
    original_pr = os.environ.get('COPILOT_AGENT_PR_NUMBER')
    
    try:
        # Set PR number
        os.environ['COPILOT_AGENT_PR_NUMBER'] = '456'
        
        # Need to reload module to pick up new env var
        import importlib
        import version_info
        importlib.reload(version_info)
        from version_info import get_version_string
        
        version_str = get_version_string()
        assert "(PR 456)" in version_str
        
    finally:
        # Restore original env
        if original_pr:
            os.environ['COPILOT_AGENT_PR_NUMBER'] = original_pr
        elif 'COPILOT_AGENT_PR_NUMBER' in os.environ:
            del os.environ['COPILOT_AGENT_PR_NUMBER']


def test_safe_check_output():
    """Test that _safe_check_output handles errors gracefully"""
    from version_info import _safe_check_output
    
    # Test with invalid command
    result = _safe_check_output(['nonexistent_command_12345'])
    assert result == ""
    
    # Test with valid command
    result = _safe_check_output(['echo', 'test'])
    assert result == "test"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
