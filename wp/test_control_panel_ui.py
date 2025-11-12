#!/usr/bin/env python3
"""
Simple validation script for control panel UI files.
Checks that all required files exist and have basic structural validity.
"""
import os
import sys

def check_file_exists(path, description):
    """Check if a file exists and print result."""
    exists = os.path.exists(path)
    status = "✓" if exists else "✗"
    print(f"{status} {description}: {path}")
    return exists

def check_file_contains(path, patterns, description):
    """Check if file contains expected patterns."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        all_found = True
        for pattern in patterns:
            if pattern not in content:
                print(f"  ✗ Missing pattern: {pattern}")
                all_found = False
        
        if all_found:
            print(f"✓ {description} contains all expected patterns")
        return all_found
    except Exception as e:
        print(f"✗ Error checking {path}: {e}")
        return False

def main():
    """Run validation checks."""
    base_dir = os.path.join(os.path.dirname(__file__), 'static', 'control-panel')
    
    print("=" * 60)
    print("Control Panel UI Validation")
    print("=" * 60)
    
    # Check file existence
    print("\n1. Checking file structure...")
    files_ok = True
    files_ok &= check_file_exists(os.path.join(base_dir, 'index.html'), "Main HTML")
    files_ok &= check_file_exists(os.path.join(base_dir, 'css', 'control-panel.css'), "CSS")
    files_ok &= check_file_exists(os.path.join(base_dir, 'js', 'main.js'), "Main JS")
    files_ok &= check_file_exists(os.path.join(base_dir, 'js', 'browse.js'), "Browse JS")
    
    if not files_ok:
        print("\n✗ Some files are missing!")
        return 1
    
    # Check HTML structure
    print("\n2. Checking HTML structure...")
    html_path = os.path.join(base_dir, 'index.html')
    html_ok = check_file_contains(
        html_path,
        [
            '<!DOCTYPE html>',
            '<head>',
            '<body>',
            'control-panel.css',
            'js/main.js',
            'js/browse.js',
            'id="apiKeySection"',
            'id="mainContent"',
            'id="browseView"',
            'id="queueView"',
            'id="settingsView"',
            'id="breadcrumbsContainer"',
            'id="filesList"',
            'id="searchInput"'
        ],
        "HTML structure"
    )
    
    # Check CSS
    print("\n3. Checking CSS...")
    css_path = os.path.join(base_dir, 'css', 'control-panel.css')
    css_ok = check_file_contains(
        css_path,
        [
            ':root',
            '--primary-color',
            '.app-container',
            '.app-header',
            '.sidebar-nav',
            '.content-area',
            '.browse-controls',
            '.breadcrumbs',
            '.file-item',
            '.file-details-drawer',
            '.state-message',
            '.btn'
        ],
        "CSS classes"
    )
    
    # Check main.js
    print("\n4. Checking main.js...")
    main_js_path = os.path.join(base_dir, 'js', 'main.js')
    main_ok = check_file_contains(
        main_js_path,
        [
            'class ControlPanel',
            'class EventBus',
            'API_KEY_STORAGE',
            'localStorage',
            'saveApiKey',
            'loadAccounts',
            'fetchAPI',
            '/api/info',
            'window.controlPanel'
        ],
        "Main JS"
    )
    
    # Check browse.js
    print("\n5. Checking browse.js...")
    browse_js_path = os.path.join(base_dir, 'js', 'browse.js')
    browse_ok = check_file_contains(
        browse_js_path,
        [
            'class BrowseModule',
            'loadDirectory',
            'performSearch',
            'renderBreadcrumbs',
            'renderFiles',
            'showFileDetails',
            '/api/files/list',
            '/api/files/search',
            'window.browseModule'
        ],
        "Browse JS"
    )
    
    # Summary
    print("\n" + "=" * 60)
    if all([files_ok, html_ok, css_ok, main_ok, browse_ok]):
        print("✓ All validation checks passed!")
        print("\nTo test the UI:")
        print("1. Start the server: python3 server.py")
        print("2. Open in browser: http://localhost:5000/static/control-panel/index.html")
        print("3. Enter your API key")
        print("4. Select an account and browse files")
        return 0
    else:
        print("✗ Some validation checks failed!")
        return 1

if __name__ == '__main__':
    sys.exit(main())
