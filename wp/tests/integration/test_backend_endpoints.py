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
