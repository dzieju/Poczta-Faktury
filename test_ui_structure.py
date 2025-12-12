#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test to verify the UI structure changes without requiring a display
"""

import sys
import os
import ast


def test_ui_structure():
    """Verify the UI structure by parsing the source code"""
    print("Test: UI Structure Verification")
    
    # Read the source file
    with open('poczta_faktury.py', 'r', encoding='utf-8') as f:
        source = f.read()
    
    # Parse the AST
    tree = ast.parse(source)
    
    # Find the create_search_tab method
    found_create_search_tab = False
    found_inner_notebook = False
    found_wyniki_tab = False
    found_znalezione_tab = False
    found_listbox = False
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if node.name == 'create_search_tab':
                found_create_search_tab = True
                # Check for inner notebook creation
                source_segment = ast.get_source_segment(source, node)
                if source_segment:
                    if 'search_inner_notebook' in source_segment:
                        found_inner_notebook = True
                    if 'text="Wyniki"' in source_segment:
                        found_wyniki_tab = True
                    if 'text="Znalezione"' in source_segment:
                        found_znalezione_tab = True
                    if 'found_live_listbox' in source_segment:
                        found_listbox = True
    
    print(f"  ✓ create_search_tab method found: {found_create_search_tab}")
    print(f"  ✓ Inner notebook created: {found_inner_notebook}")
    print(f"  ✓ 'Wyniki' tab exists: {found_wyniki_tab}")
    print(f"  ✓ 'Znalezione' tab exists: {found_znalezione_tab}")
    print(f"  ✓ Live listbox created: {found_listbox}")
    
    return all([
        found_create_search_tab,
        found_inner_notebook,
        found_wyniki_tab,
        found_znalezione_tab,
        found_listbox
    ])


def test_polling_mechanism():
    """Verify the polling mechanism handles both log and found messages"""
    print("\nTest: Polling Mechanism")
    
    with open('poczta_faktury.py', 'r', encoding='utf-8') as f:
        source = f.read()
    
    # Check for the updated _poll_log_queue method
    has_poll_method = '_poll_log_queue' in source
    handles_log_type = "item.get('type') == 'log'" in source
    handles_found_type = "item.get('type') == 'found'" in source
    updates_listbox = 'found_live_listbox.insert' in source
    
    print(f"  ✓ _poll_log_queue method exists: {has_poll_method}")
    print(f"  ✓ Handles 'log' type messages: {handles_log_type}")
    print(f"  ✓ Handles 'found' type messages: {handles_found_type}")
    print(f"  ✓ Updates live listbox: {updates_listbox}")
    
    return all([
        has_poll_method,
        handles_log_type,
        handles_found_type,
        updates_listbox
    ])


def test_search_worker_module():
    """Verify the search_worker module exists and has required classes"""
    print("\nTest: Search Worker Module")
    
    # Check if file exists
    worker_exists = os.path.exists('search_worker.py')
    print(f"  ✓ search_worker.py exists: {worker_exists}")
    
    if worker_exists:
        with open('search_worker.py', 'r', encoding='utf-8') as f:
            source = f.read()
        
        has_search_stop = 'class SearchStop' in source
        print(f"  ✓ SearchStop class exists: {has_search_stop}")
        
        return worker_exists and has_search_stop
    
    return worker_exists


def test_live_result_push():
    """Verify that found files are pushed to the queue immediately"""
    print("\nTest: Live Result Push")
    
    with open('poczta_faktury.py', 'r', encoding='utf-8') as f:
        source = f.read()
    
    # Look for the code that pushes found results to queue
    pushes_found_to_queue = "self.log_queue.put({" in source and "'type': 'found'" in source
    pushes_in_imap_search = "_search_with_imap_threaded" in source
    
    print(f"  ✓ Pushes found files to queue: {pushes_found_to_queue}")
    print(f"  ✓ IMAP search method exists: {pushes_in_imap_search}")
    
    return all([
        pushes_found_to_queue,
        pushes_in_imap_search
    ])


def test_create_widgets_update():
    """Verify create_widgets was updated to remove old 'Znalezione' top-level tab"""
    print("\nTest: create_widgets Update")
    
    with open('poczta_faktury.py', 'r', encoding='utf-8') as f:
        source = f.read()
    
    tree = ast.parse(source)
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == 'create_widgets':
            # Count notebook.add calls using AST traversal
            num_adds = 0
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    if isinstance(child.func, ast.Attribute):
                        if child.func.attr == 'add' and isinstance(child.func.value, ast.Attribute):
                            if child.func.value.attr == 'notebook':
                                num_adds += 1
            
            # Should be 3: Konfiguracja poczty, Wyszukiwanie NIP, O programie
            correct_tab_count = num_adds == 3
            
            # Verify no direct "Znalezione" tab at top level by checking the source
            source_segment = ast.get_source_segment(source, node) or ""
            no_top_level_znalezione = 'text="Znalezione"' not in source_segment
            
            print(f"  ✓ Correct number of top-level tabs (3): {correct_tab_count} (found {num_adds})")
            print(f"  ✓ No top-level 'Znalezione' tab: {no_top_level_znalezione}")
            
            return correct_tab_count and no_top_level_znalezione
    
    return False


def main():
    print("=" * 60)
    print("UI STRUCTURE TESTS")
    print("=" * 60)
    print()
    
    results = []
    
    results.append(test_ui_structure())
    results.append(test_polling_mechanism())
    results.append(test_search_worker_module())
    results.append(test_live_result_push())
    results.append(test_create_widgets_update())
    
    print()
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"RESULTS: {passed}/{total} tests passed")
    print("=" * 60)
    
    return all(results)


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
