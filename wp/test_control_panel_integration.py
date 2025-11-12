#!/usr/bin/env python3
"""
Integration test for control panel functionality
Tests the SPA routes, API endpoints, and JavaScript modules integration
"""
import os
import sys
import json

# Add the wp directory to the path
sys.path.insert(0, os.path.dirname(__file__))

def test_control_panel_spa():
    """Test control panel SPA serving"""
    from server import app
    
    print("\n" + "=" * 70)
    print("Testing Control Panel SPA")
    print("=" * 70)
    
    with app.test_client() as client:
        # Test index route
        print("\n1. Testing /control route...")
        response = client.get('/control')
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert b'Control Panel' in response.data or b'control-panel' in response.data.lower(), "Missing control panel content"
        print("   ✓ /control serves index.html")
        
        # Test alternate index route
        response = client.get('/control/')
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("   ✓ /control/ serves index.html")
        
        # Test CSS asset
        print("\n2. Testing CSS asset serving...")
        response = client.get('/control/css/control-panel.css')
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert b'--primary-color' in response.data or b'primary' in response.data, "CSS content missing"
        print("   ✓ /control/css/control-panel.css serves correctly")
        
        # Test JS assets
        print("\n3. Testing JavaScript asset serving...")
        js_files = ['main.js', 'browse.js', 'queue.js', 'settings.js']
        for js_file in js_files:
            response = client.get(f'/control/js/{js_file}')
            assert response.status_code == 200, f"Expected 200 for {js_file}, got {response.status_code}"
            print(f"   ✓ /control/js/{js_file} serves correctly")
    
    print("\n✓ All SPA routes working correctly")

def test_overview_endpoint():
    """Test the /api/control/overview endpoint"""
    from server import app, config
    
    print("\n" + "=" * 70)
    print("Testing /api/control/overview Endpoint")
    print("=" * 70)
    
    with app.test_client() as client:
        # Test without API key
        print("\n1. Testing without API key...")
        response = client.get('/api/control/overview')
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("   ✓ Returns 401 without API key")
        
        # Test with API key
        print("\n2. Testing with API key...")
        headers = {'X-API-Key': config.API_SECRET_KEY}
        response = client.get('/api/control/overview', headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = json.loads(response.data)
        assert data.get('success') == True, "Response should be successful"
        assert 'data' in data, "Response should contain data"
        
        overview_data = data['data']
        assert 'health' in overview_data, "Overview should contain health"
        assert 'accounts' in overview_data, "Overview should contain accounts"
        assert 'queues_summary' in overview_data, "Overview should contain queues_summary"
        
        print("   ✓ Returns 200 with API key")
        print("   ✓ Response structure is correct")
        
        # Check queues_summary structure
        print("\n3. Testing queues_summary structure...")
        summary = overview_data['queues_summary']
        required_fields = [
            'total_accounts',
            'total_transfer_pending',
            'total_transfer_running',
            'total_transfer_completed',
            'total_transfer_failed',
            'total_share_pending',
            'total_share_running',
            'total_share_completed',
            'total_share_failed'
        ]
        
        for field in required_fields:
            assert field in summary, f"Missing field: {field}"
            print(f"   ✓ {field}: {summary[field]}")
    
    print("\n✓ Overview endpoint working correctly")

def test_html_structure():
    """Test that HTML contains all required elements"""
    print("\n" + "=" * 70)
    print("Testing HTML Structure")
    print("=" * 70)
    
    html_path = os.path.join(os.path.dirname(__file__), 'static', 'control-panel', 'index.html')
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    required_elements = [
        ('dashboardSummary', 'Dashboard summary section'),
        ('dashTransferPending', 'Dashboard transfer pending stat'),
        ('dashTransferRunning', 'Dashboard transfer running stat'),
        ('dashSharePending', 'Dashboard share pending stat'),
        ('dashShareRunning', 'Dashboard share running stat'),
        ('refreshDashboardBtn', 'Dashboard refresh button'),
        ('browseView', 'Browse tab view'),
        ('queueView', 'Queue tab view'),
        ('settingsView', 'Settings tab view'),
    ]
    
    print("\nChecking for required HTML elements:")
    for element_id, description in required_elements:
        assert element_id in html_content, f"Missing element: {element_id}"
        print(f"   ✓ {description} ({element_id})")
    
    print("\n✓ HTML structure is complete")

def test_javascript_modules():
    """Test that JavaScript modules are properly structured"""
    print("\n" + "=" * 70)
    print("Testing JavaScript Modules")
    print("=" * 70)
    
    js_dir = os.path.join(os.path.dirname(__file__), 'static', 'control-panel', 'js')
    
    # Check main.js
    print("\n1. Checking main.js...")
    with open(os.path.join(js_dir, 'main.js'), 'r', encoding='utf-8') as f:
        main_content = f.read()
    
    main_required = [
        'class ControlPanel',
        'class EventBus',
        'switchTab',
        'loadDashboard',
        'renderDashboard',
        'getAutoRefreshInterval',
        'window.controlPanel'
    ]
    
    for item in main_required:
        assert item in main_content, f"Missing in main.js: {item}"
        print(f"   ✓ {item}")
    
    # Check queue.js
    print("\n2. Checking queue.js...")
    with open(os.path.join(js_dir, 'queue.js'), 'r', encoding='utf-8') as f:
        queue_content = f.read()
    
    queue_required = [
        'class QueueManager',
        'startAutoRefresh',
        'stopAutoRefresh',
        'getRefreshInterval',
        'settingsUpdated'
    ]
    
    for item in queue_required:
        assert item in queue_content, f"Missing in queue.js: {item}"
        print(f"   ✓ {item}")
    
    # Check settings.js
    print("\n3. Checking settings.js...")
    with open(os.path.join(js_dir, 'settings.js'), 'r', encoding='utf-8') as f:
        settings_content = f.read()
    
    settings_required = [
        'loadSettings',
        'saveSettings',
        'window.controlPanel.eventBus',
        'settingsUpdated'
    ]
    
    for item in settings_required:
        assert item in settings_content, f"Missing in settings.js: {item}"
        print(f"   ✓ {item}")
    
    print("\n✓ JavaScript modules are properly structured")

def test_css_responsive():
    """Test that CSS includes responsive styles"""
    print("\n" + "=" * 70)
    print("Testing CSS Responsive Design")
    print("=" * 70)
    
    css_path = os.path.join(os.path.dirname(__file__), 'static', 'control-panel', 'css', 'control-panel.css')
    with open(css_path, 'r', encoding='utf-8') as f:
        css_content = f.read()
    
    responsive_checks = [
        ('@media', 'Media queries for responsive design'),
        ('dashboard-summary', 'Dashboard summary styles'),
        ('stat-item', 'Stat item styles'),
        ('stat-value', 'Stat value styles'),
    ]
    
    print("\nChecking for responsive design features:")
    for check, description in responsive_checks:
        assert check in css_content, f"Missing CSS: {check}"
        print(f"   ✓ {description} ({check})")
    
    print("\n✓ CSS includes responsive design")

def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("CONTROL PANEL INTEGRATION TEST SUITE")
    print("=" * 70)
    
    try:
        test_control_panel_spa()
        test_overview_endpoint()
        test_html_structure()
        test_javascript_modules()
        test_css_responsive()
        
        print("\n" + "=" * 70)
        print("✓ ALL TESTS PASSED!")
        print("=" * 70)
        print("\nControl Panel Features Verified:")
        print("  ✓ Flask routes for /control SPA")
        print("  ✓ /api/control/overview endpoint")
        print("  ✓ Tab navigation system")
        print("  ✓ Dashboard with quick stats")
        print("  ✓ Shared state via EventBus")
        print("  ✓ Module initialization/cleanup")
        print("  ✓ Auto-refresh interval configuration")
        print("  ✓ Responsive layout")
        print("=" * 70 + "\n")
        
        return 0
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
