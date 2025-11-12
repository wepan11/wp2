#!/usr/bin/env python3
"""
Test script to verify control panel routes and functionality
"""
import os
import sys

# Add the wp directory to the path
sys.path.insert(0, os.path.dirname(__file__))

def test_routes():
    """Test that all control panel routes are properly registered"""
    from server import app
    
    print("Testing Control Panel Routes...")
    print("=" * 50)
    
    # Get all routes
    routes = []
    for rule in app.url_map.iter_rules():
        if 'control' in rule.rule:
            routes.append({
                'endpoint': rule.endpoint,
                'methods': ','.join(rule.methods - {'HEAD', 'OPTIONS'}),
                'path': rule.rule
            })
    
    print("\nControl Panel Routes:")
    for route in sorted(routes, key=lambda x: x['path']):
        print(f"  {route['methods']:10} {route['path']:40} -> {route['endpoint']}")
    
    # Check required routes exist
    required_routes = [
        '/control',
        '/control/',
        '/control/<path:path>',
        '/api/control/overview',
        '/api/control/queues',
        '/api/control/settings'
    ]
    
    found_routes = [r['path'] for r in routes]
    
    print("\nRequired Routes Check:")
    all_found = True
    for req_route in required_routes:
        found = any(req_route in fr for fr in found_routes)
        status = "✓" if found else "✗"
        print(f"  {status} {req_route}")
        if not found:
            all_found = False
    
    # Check static files exist
    print("\nStatic Files Check:")
    static_dir = os.path.join(os.path.dirname(__file__), 'static', 'control-panel')
    
    required_files = [
        'index.html',
        'css/control-panel.css',
        'js/main.js',
        'js/browse.js',
        'js/queue.js',
        'js/settings.js'
    ]
    
    all_files_exist = True
    for file in required_files:
        file_path = os.path.join(static_dir, file)
        exists = os.path.exists(file_path)
        status = "✓" if exists else "✗"
        print(f"  {status} {file}")
        if not exists:
            all_files_exist = False
    
    print("\n" + "=" * 50)
    if all_found and all_files_exist:
        print("✓ All checks passed!")
        return 0
    else:
        print("✗ Some checks failed!")
        return 1

if __name__ == '__main__':
    sys.exit(test_routes())
