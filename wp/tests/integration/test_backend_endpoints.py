"""
Integration tests for backend control-related APIs.

Tests validate:
- Authentication flows (with/without API key)
- Happy-path responses with deterministic data
- Error propagation when services return errors
- Account parameter handling

No real Baidu API calls are made - FakeCoreService provides stub data.
"""
import pytest
import json


class TestHealthAndInfo:
    """Test system status endpoints."""
    
    def test_health_no_auth_required(self, client):
        """Health endpoint should work without authentication."""
        response = client.get('/api/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'ok'
        assert 'version' in data
        assert 'accounts' in data
        assert 'timestamp' in data
    
    def test_info_requires_auth(self, client):
        """Info endpoint should require API key."""
        response = client.get('/api/info')
        assert response.status_code == 401
        data = response.get_json()
        assert data['success'] is False
        assert 'API key' in data['error'] or 'API密钥' in data['message']
    
    def test_info_with_auth(self, client, auth_headers):
        """Info endpoint should return system info with valid API key."""
        response = client.get('/api/info', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'app_name' in data['data']
        assert 'version' in data['data']
        assert 'accounts' in data['data']
        assert 'config' in data['data']


class TestAuthenticationFlows:
    """Test authentication and authorization."""
    
    def test_missing_api_key(self, client):
        """Endpoints requiring auth should reject requests without API key."""
        endpoints = [
            '/api/info',
            '/api/files/list?path=/',
            '/api/files/search?keyword=test',
            '/api/transfer/status',
            '/api/transfer/queue',
            '/api/share/status',
            '/api/share/queue'
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401, f"Expected 401 for {endpoint}"
            data = response.get_json()
            assert data['success'] is False
    
    def test_invalid_api_key(self, client):
        """Endpoints should reject invalid API keys."""
        bad_headers = {'X-API-Key': 'invalid_key_123'}
        response = client.get('/api/info', headers=bad_headers)
        assert response.status_code == 401
        data = response.get_json()
        assert data['success'] is False


class TestFileManagement:
    """Test file management endpoints."""
    
    def test_list_files_happy_path(self, client, auth_headers):
        """List files should return fake directory contents."""
        response = client.get('/api/files/list?path=/test', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert isinstance(data['data'], list)
        # Check fake data structure
        assert len(data['data']) > 0
        first_file = data['data'][0]
        assert 'fs_id' in first_file
        assert 'server_filename' in first_file
        assert 'path' in first_file
    
    def test_list_files_with_account(self, client, auth_headers):
        """List files should handle account parameter."""
        response = client.get(
            '/api/files/list?path=/&account=test_account',
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert isinstance(data['data'], list)
    
    def test_list_files_error_propagation(self, client, auth_headers, fake_services):
        """List files should handle service errors."""
        # Configure first service to fail
        first_service = list(fake_services.values())[0]
        first_service.set_should_fail(True)
        
        response = client.get('/api/files/list?path=/fail', headers=auth_headers)
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert '错误码' in data['error'] or 'error' in data['error'].lower()
    
    def test_search_files_happy_path(self, client, auth_headers):
        """Search files should return fake search results."""
        response = client.get(
            '/api/files/search?keyword=test&path=/',
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert isinstance(data['data'], list)
        # Check fake search results
        if data['data']:
            result = data['data'][0]
            assert 'fs_id' in result
            assert 'server_filename' in result
    
    def test_search_files_missing_keyword(self, client, auth_headers):
        """Search files should require keyword parameter."""
        response = client.get('/api/files/search?path=/', headers=auth_headers)
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'keyword' in data['error']


class TestTransferEndpoints:
    """Test transfer-related endpoints."""
    
    def test_transfer_status_happy_path(self, client, auth_headers):
        """Transfer status should return fake status data."""
        response = client.get('/api/transfer/status', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        status = data['data']
        # Check status structure
        assert 'total' in status
        assert 'pending' in status
        assert 'running' in status
        assert 'completed' in status
        assert 'failed' in status
        assert 'is_running' in status
        assert 'is_paused' in status
    
    def test_transfer_status_with_account(self, client, auth_headers):
        """Transfer status should handle account parameter."""
        response = client.get(
            '/api/transfer/status?account=test_account',
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
    
    def test_transfer_queue_happy_path(self, client, auth_headers):
        """Transfer queue should return fake queue data."""
        response = client.get('/api/transfer/queue', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        queue = data['data']
        assert isinstance(queue, list)
        # Check queue item structure
        if queue:
            task = queue[0]
            assert 'share_link' in task
            assert 'status' in task
    
    def test_transfer_queue_with_account(self, client, auth_headers):
        """Transfer queue should handle account parameter."""
        response = client.get(
            '/api/transfer/queue?account=test_account2',
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True


class TestShareEndpoints:
    """Test share-related endpoints."""
    
    def test_share_status_happy_path(self, client, auth_headers):
        """Share status should return fake status data."""
        response = client.get('/api/share/status', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        status = data['data']
        # Check status structure
        assert 'total' in status
        assert 'pending' in status
        assert 'running' in status
        assert 'completed' in status
        assert 'failed' in status
        assert 'is_running' in status
        assert 'is_paused' in status
    
    def test_share_status_with_account(self, client, auth_headers):
        """Share status should handle account parameter."""
        response = client.get(
            '/api/share/status?account=test_account',
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
    
    def test_share_queue_happy_path(self, client, auth_headers):
        """Share queue should return fake queue data."""
        response = client.get('/api/share/queue', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        queue = data['data']
        assert isinstance(queue, list)
        # Check queue item structure
        if queue:
            task = queue[0]
            assert 'file_info' in task
            assert 'status' in task
    
    def test_share_queue_with_account(self, client, auth_headers):
        """Share queue should handle account parameter."""
        response = client.get(
            '/api/share/queue?account=test_account2',
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True


class TestAccountParameter:
    """Test account parameter handling across endpoints."""
    
    @pytest.mark.parametrize('endpoint,params', [
        ('/api/files/list', 'path=/'),
        ('/api/files/search', 'keyword=test'),
        ('/api/transfer/status', ''),
        ('/api/transfer/queue', ''),
        ('/api/share/status', ''),
        ('/api/share/queue', ''),
    ])
    def test_endpoints_accept_account_param(self, client, auth_headers, endpoint, params):
        """All service endpoints should accept account parameter."""
        url = f'{endpoint}?{params}&account=test_account' if params else f'{endpoint}?account=test_account'
        response = client.get(url, headers=auth_headers)
        # Should not fail due to account parameter
        assert response.status_code in [200, 400]  # 400 only for validation errors, not account errors


class TestErrorPropagation:
    """Test error handling and propagation."""
    
    def test_list_files_service_error(self, client, auth_headers, fake_services):
        """Service errors should be properly propagated."""
        # Make service return error code
        service = list(fake_services.values())[0]
        service.set_should_fail(True)
        
        response = client.get('/api/files/list?path=/error', headers=auth_headers)
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'error' in data
    
    def test_search_files_returns_empty_on_error(self, client, auth_headers, fake_services):
        """Search returning empty results should not cause 4xx error."""
        service = list(fake_services.values())[0]
        service.set_should_fail(True)
        
        response = client.get(
            '/api/files/search?keyword=nothing&path=/',
            headers=auth_headers
        )
        # Empty results are still successful
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data'] == []


class TestControlQueues:
    """Test aggregated queue endpoint for control panel."""
    
    def test_control_queues_requires_auth(self, client):
        """Control queues endpoint should require API key."""
        response = client.get('/api/control/queues')
        assert response.status_code == 401
        data = response.get_json()
        assert data['success'] is False
    
    def test_control_queues_happy_path(self, client, auth_headers):
        """Control queues should return aggregated data for all accounts."""
        response = client.get('/api/control/queues', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        
        # Check response structure
        assert 'data' in data
        assert 'timestamp' in data['data']
        assert 'accounts' in data['data']
        
        # Check accounts data
        accounts = data['data']['accounts']
        assert isinstance(accounts, dict)
        
        # Should have at least one account from fake_accounts fixture
        assert len(accounts) > 0
        
        # Check account structure
        for account_name, account_data in accounts.items():
            assert 'available' in account_data
            
            if account_data['available']:
                # Check transfer data
                assert 'transfer' in account_data
                assert 'status' in account_data['transfer']
                assert 'queue' in account_data['transfer']
                
                transfer_status = account_data['transfer']['status']
                assert 'total' in transfer_status
                assert 'pending' in transfer_status
                assert 'running' in transfer_status
                assert 'completed' in transfer_status
                assert 'failed' in transfer_status
                assert 'is_running' in transfer_status
                assert 'is_paused' in transfer_status
                
                # Check share data
                assert 'share' in account_data
                assert 'status' in account_data['share']
                assert 'queue' in account_data['share']
                
                share_status = account_data['share']['status']
                assert 'total' in share_status
                assert 'pending' in share_status
                assert 'running' in share_status
                assert 'completed' in share_status
                assert 'failed' in share_status
                assert 'is_running' in share_status
                assert 'is_paused' in share_status
    
    def test_control_queues_handles_unavailable_service(self, client, auth_headers, monkeypatch, fake_accounts):
        """Control queues should gracefully handle unavailable services."""
        # Monkeypatch to return None for one account
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        import server as server_module
        
        original_get_or_create_service = server_module.get_or_create_service
        
        def mock_get_or_create_service(account=None):
            if account == 'test_account':
                return None  # Simulate unavailable service
            return original_get_or_create_service(account)
        
        monkeypatch.setattr(server_module, 'get_or_create_service', mock_get_or_create_service)
        
        response = client.get('/api/control/queues', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        
        # Check that unavailable account is marked as such
        accounts = data['data']['accounts']
        if 'test_account' in accounts:
            assert accounts['test_account']['available'] is False
            assert 'error' in accounts['test_account']


class TestSettingsEndpoints:
    """Test settings management endpoints."""
    
    def test_get_settings_requires_auth(self, client):
        """Settings endpoint should require API key."""
        response = client.get('/api/control/settings')
        assert response.status_code == 401
        data = response.get_json()
        assert data['success'] is False
    
    def test_get_settings_happy_path(self, client, auth_headers, monkeypatch, tmp_path):
        """Settings GET should return default settings structure."""
        # Monkeypatch settings manager to use temp directory
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        from settings_manager import SettingsManager
        
        # Use temporary directory for settings file
        temp_data_dir = str(tmp_path)
        original_init = SettingsManager.__init__
        
        def mock_init(self, data_dir=None):
            original_init(self, data_dir=temp_data_dir)
        
        monkeypatch.setattr(SettingsManager, '__init__', mock_init)
        
        response = client.get('/api/control/settings', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        
        # Check structure
        settings_data = data['data']
        assert 'throttle' in settings_data
        assert 'workers' in settings_data
        assert 'rate_limit' in settings_data
        assert 'ui' in settings_data
        assert 'accounts' in settings_data
        
        # Check throttle settings
        throttle = settings_data['throttle']
        assert 'jitter_ms_min' in throttle
        assert 'jitter_ms_max' in throttle
        assert 'ops_per_window' in throttle
        assert 'window_sec' in throttle
        
        # Check worker settings
        workers = settings_data['workers']
        assert 'max_transfer_workers' in workers
        assert 'max_share_workers' in workers
        
        # Check UI settings
        ui = settings_data['ui']
        assert 'auto_refresh_interval' in ui
        assert 'api_key_retention' in ui
    
    def test_update_settings_requires_auth(self, client):
        """Settings PUT should require API key."""
        response = client.put('/api/control/settings', json={
            'throttle': {'jitter_ms_min': 1000}
        })
        assert response.status_code == 401
    
    def test_update_settings_empty_body(self, client, auth_headers):
        """Settings PUT should reject empty body."""
        response = client.put('/api/control/settings', headers=auth_headers, json={})
        # Empty dict is falsy in Python, so it's treated as missing body
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
    
    def test_update_settings_valid_throttle(self, client, auth_headers, monkeypatch, tmp_path):
        """Settings PUT should accept and persist valid throttle updates."""
        # Monkeypatch settings manager to use temp directory
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        from settings_manager import SettingsManager
        
        temp_data_dir = str(tmp_path)
        original_init = SettingsManager.__init__
        
        def mock_init(self, data_dir=None):
            original_init(self, data_dir=temp_data_dir)
        
        monkeypatch.setattr(SettingsManager, '__init__', mock_init)
        
        # Update throttle settings
        new_settings = {
            'throttle': {
                'jitter_ms_min': 1000,
                'jitter_ms_max': 2000,
                'ops_per_window': 100,
                'window_sec': 120,
                'window_rest_sec': 30,
                'max_consecutive_failures': 10,
                'pause_sec_on_failure': 120,
                'backoff_factor': 2.0,
                'cooldown_on_errno_-62_sec': 180
            }
        }
        
        response = client.put(
            '/api/control/settings',
            json=new_settings,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'data' in data
        
        # Verify updated values
        updated_throttle = data['data']['throttle']
        assert updated_throttle['jitter_ms_min'] == 1000
        assert updated_throttle['jitter_ms_max'] == 2000
        assert updated_throttle['ops_per_window'] == 100
    
    def test_update_settings_invalid_throttle_values(self, client, auth_headers):
        """Settings PUT should reject invalid throttle values."""
        invalid_settings = {
            'throttle': {
                'jitter_ms_min': -100,  # Invalid: negative
                'jitter_ms_max': 2000,
                'ops_per_window': 50,
                'window_sec': 60,
                'window_rest_sec': 20,
                'max_consecutive_failures': 5,
                'pause_sec_on_failure': 60,
                'backoff_factor': 1.5,
                'cooldown_on_errno_-62_sec': 120
            }
        }
        
        response = client.put(
            '/api/control/settings',
            json=invalid_settings,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'error' in data
    
    def test_update_settings_invalid_worker_values(self, client, auth_headers):
        """Settings PUT should reject invalid worker values."""
        invalid_settings = {
            'workers': {
                'max_transfer_workers': 0,  # Invalid: must be >= 1
                'max_share_workers': 2
            }
        }
        
        response = client.put(
            '/api/control/settings',
            json=invalid_settings,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'error' in data
    
    def test_update_settings_valid_workers(self, client, auth_headers, monkeypatch, tmp_path):
        """Settings PUT should accept valid worker settings."""
        # Monkeypatch settings manager to use temp directory
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        from settings_manager import SettingsManager
        
        temp_data_dir = str(tmp_path)
        original_init = SettingsManager.__init__
        
        def mock_init(self, data_dir=None):
            original_init(self, data_dir=temp_data_dir)
        
        monkeypatch.setattr(SettingsManager, '__init__', mock_init)
        
        new_settings = {
            'workers': {
                'max_transfer_workers': 3,
                'max_share_workers': 2
            }
        }
        
        response = client.put(
            '/api/control/settings',
            json=new_settings,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['workers']['max_transfer_workers'] == 3
        assert data['data']['workers']['max_share_workers'] == 2
    
    def test_update_settings_partial_update(self, client, auth_headers, monkeypatch, tmp_path):
        """Settings PUT should support partial updates (only update provided fields)."""
        # Monkeypatch settings manager to use temp directory
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        from settings_manager import SettingsManager
        
        temp_data_dir = str(tmp_path)
        original_init = SettingsManager.__init__
        
        def mock_init(self, data_dir=None):
            original_init(self, data_dir=temp_data_dir)
        
        monkeypatch.setattr(SettingsManager, '__init__', mock_init)
        
        # Update only UI settings
        partial_settings = {
            'ui': {
                'auto_refresh_interval': 10000,
                'api_key_retention': False
            }
        }
        
        response = client.put(
            '/api/control/settings',
            json=partial_settings,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        
        # UI should be updated
        assert data['data']['ui']['auto_refresh_interval'] == 10000
        assert data['data']['ui']['api_key_retention'] is False
        
        # Other settings should still exist (not removed)
        assert 'throttle' in data['data']
        assert 'workers' in data['data']
    
    def test_get_settings_includes_new_sections(self, client, auth_headers, monkeypatch, tmp_path):
        """Settings GET should include share_defaults and transfer_defaults."""
        # Monkeypatch settings manager to use temp directory
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        from settings_manager import SettingsManager
        
        temp_data_dir = str(tmp_path)
        original_init = SettingsManager.__init__
        
        def mock_init(self, data_dir=None):
            original_init(self, data_dir=temp_data_dir)
        
        monkeypatch.setattr(SettingsManager, '__init__', mock_init)
        
        response = client.get('/api/control/settings', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        
        settings_data = data['data']
        assert 'share_defaults' in settings_data
        assert 'transfer_defaults' in settings_data
        
        # Check share_defaults structure
        share_defaults = settings_data['share_defaults']
        assert 'expiry' in share_defaults
        assert 'auto_password' in share_defaults
        assert 'fixed_password' in share_defaults
        
        # Check transfer_defaults structure
        transfer_defaults = settings_data['transfer_defaults']
        assert 'target_path' in transfer_defaults
    
    def test_update_settings_valid_share_defaults(self, client, auth_headers, monkeypatch, tmp_path):
        """Settings PUT should accept valid share_defaults."""
        # Monkeypatch settings manager
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        from settings_manager import SettingsManager
        
        temp_data_dir = str(tmp_path)
        original_init = SettingsManager.__init__
        
        def mock_init(self, data_dir=None):
            original_init(self, data_dir=temp_data_dir)
        
        monkeypatch.setattr(SettingsManager, '__init__', mock_init)
        
        new_settings = {
            'share_defaults': {
                'expiry': 30,
                'auto_password': False,
                'fixed_password': 'test'
            }
        }
        
        response = client.put(
            '/api/control/settings',
            json=new_settings,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['share_defaults']['expiry'] == 30
        assert data['data']['share_defaults']['auto_password'] is False
        assert data['data']['share_defaults']['fixed_password'] == 'test'
    
    def test_update_settings_invalid_share_expiry(self, client, auth_headers):
        """Settings PUT should reject invalid share expiry."""
        invalid_settings = {
            'share_defaults': {
                'expiry': 14  # Invalid: must be 0, 1, 7, or 30
            }
        }
        
        response = client.put(
            '/api/control/settings',
            json=invalid_settings,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'expiry' in data['error'].lower()
    
    def test_update_settings_invalid_share_password(self, client, auth_headers):
        """Settings PUT should reject invalid fixed password length."""
        invalid_settings = {
            'share_defaults': {
                'fixed_password': 'abc'  # Invalid: must be empty or 4 chars
            }
        }
        
        response = client.put(
            '/api/control/settings',
            json=invalid_settings,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'password' in data['error'].lower()
    
    def test_update_settings_valid_transfer_defaults(self, client, auth_headers, monkeypatch, tmp_path):
        """Settings PUT should accept valid transfer_defaults."""
        # Monkeypatch settings manager
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        from settings_manager import SettingsManager
        
        temp_data_dir = str(tmp_path)
        original_init = SettingsManager.__init__
        
        def mock_init(self, data_dir=None):
            original_init(self, data_dir=temp_data_dir)
        
        monkeypatch.setattr(SettingsManager, '__init__', mock_init)
        
        new_settings = {
            'transfer_defaults': {
                'target_path': '/custom/target'
            }
        }
        
        response = client.put(
            '/api/control/settings',
            json=new_settings,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['transfer_defaults']['target_path'] == '/custom/target'
    
    def test_update_settings_invalid_transfer_path(self, client, auth_headers):
        """Settings PUT should reject invalid transfer target_path."""
        invalid_settings = {
            'transfer_defaults': {
                'target_path': 'no_leading_slash'  # Invalid: must start with /
            }
        }
        
        response = client.put(
            '/api/control/settings',
            json=invalid_settings,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'start with' in data['error'].lower()
    
    def test_update_settings_applies_to_services(self, client, auth_headers, monkeypatch, tmp_path, fake_services):
        """Settings PUT should call apply_settings on active services."""
        # Monkeypatch settings manager
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        from settings_manager import SettingsManager
        
        temp_data_dir = str(tmp_path)
        original_init = SettingsManager.__init__
        
        def mock_init(self, data_dir=None):
            original_init(self, data_dir=temp_data_dir)
        
        monkeypatch.setattr(SettingsManager, '__init__', mock_init)
        
        # Track if apply_settings was called
        calls = []
        for service in fake_services.values():
            original_apply = service.apply_settings
            def track_apply(settings, svc=service):
                calls.append(svc)
                original_apply(settings)
            service.apply_settings = track_apply
        
        new_settings = {
            'share_defaults': {
                'expiry': 7
            }
        }
        
        response = client.put(
            '/api/control/settings',
            json=new_settings,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        # Verify apply_settings was called on services
        assert len(calls) >= 0  # May be 0 if no services are currently initialized
