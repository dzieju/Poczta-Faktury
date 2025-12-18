#!/usr/bin/env python3
"""
Utilities to detect PR number and build a version string.
Lightweight adaptation of the approach used in Czytnik-OCR.
"""

import os
import re
import subprocess
from pathlib import Path
from typing import Optional

def _safe_check_output(cmd, timeout=3):
    try:
        return subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True, timeout=timeout).strip()
    except Exception:
        return ""

def get_pr_number_from_git_log() -> Optional[str]:
    """Try to extract PR number from merge commit message in git log."""
    try:
        git_log = _safe_check_output(['git', 'log', '--all', '--grep=Merge pull request #', '--pretty=format:%s', '-1'])
        if git_log:
            m = re.search(r'Merge pull request #(\d+)', git_log)
            if m:
                return m.group(1)
    except Exception:
        pass
    return None

def get_pr_number() -> Optional[str]:
    """
    Try multiple methods to determine PR number:
    1) environment variables (COPILOT_AGENT_PR_NUMBER, GITHUB_PR_NUMBER)
    2) GITHUB_REF (refs/pull/<num>/...)
    3) branch name pattern (pr-123 / PR123)
    4) git log merge commit
    Returns PR number as string or None.
    """
    try:
        pr = os.environ.get('COPILOT_AGENT_PR_NUMBER', '').strip()
        if pr:
            return pr
        pr = os.environ.get('GITHUB_PR_NUMBER', '').strip()
        if pr:
            return pr

        github_ref = os.environ.get('GITHUB_REF', '')
        m = re.search(r'refs/pull/(\d+)/', github_ref)
        if m:
            return m.group(1)

        # branch name
        branch = _safe_check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'])
        if branch:
            m = re.search(r'pr[-_]?(\d+)', branch, re.IGNORECASE)
            if m:
                return m.group(1)

        # fallback to git log merge
        return get_pr_number_from_git_log()
    except Exception:
        return None

def get_version_string() -> str:
    """
    Build a version string. If version.txt exists, read it; otherwise 'dev'.
    If PR number is found, append it as '(PR <num>)'.
    Examples:
      'ver. 1.2.3 (PR 42)'
      'ver. dev'
    """
    try:
        version_file = Path(__file__).parent / 'version.txt'
        if version_file.exists():
            version = version_file.read_text(encoding='utf-8').strip()
            if not version:
                version = 'dev'
        else:
            version = 'dev'
    except Exception:
        version = 'dev'

    pr = get_pr_number()
    if pr:
        return f"ver. {version} (PR {pr})"
    else:
        return f"ver. {version}"
