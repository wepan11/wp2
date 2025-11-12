# Integration Tests for Backend Control APIs

This directory contains integration tests for the backend control-related APIs, ensuring no regressions before building new UI layers.

## Overview

The integration tests validate:
- Authentication flows (with/without API key)
- Happy-path responses with deterministic data
- Error propagation when services return errors
- Account parameter handling

**No real Baidu API calls are made** - all tests use `FakeCoreService` stubs.

## Running Tests

Run all integration tests:
```bash
pytest tests/integration
```

Run with verbose output:
```bash
pytest tests/integration -v
```

Run specific test class:
```bash
pytest tests/integration/test_backend_endpoints.py::TestFileManagement -v
```

## Test Structure

### `conftest.py`
Contains pytest fixtures and `FakeCoreService` implementation:
- `FakeCoreService`: Lightweight stub that responds to CoreService methods with deterministic data
- `app_with_fakes`: Flask test app with monkeypatched account loading and service creation
- `client`: Flask test client fixture
- `auth_headers`: Pre-configured authentication headers

### `test_backend_endpoints.py`
Contains test classes for each API group:
- `TestHealthAndInfo`: System status endpoints
- `TestAuthenticationFlows`: Auth/authorization tests
- `TestFileManagement`: File listing and search
- `TestTransferEndpoints`: Transfer status and queue
- `TestShareEndpoints`: Share status and queue
- `TestAccountParameter`: Account parameter handling
- `TestErrorPropagation`: Error handling tests

## Extending for New Control Panel Endpoints

When adding new control panel endpoints, follow these steps:

### 1. Add Method to FakeCoreService

In `conftest.py`, add the corresponding method to `FakeCoreService`:

```python
class FakeCoreService:
    # ... existing methods ...
    
    def new_endpoint_method(self, param1, param2) -> Dict[str, Any]:
        """Return fake data for new endpoint."""
        if self._should_fail:
            raise Exception("Simulated error")
        return {
            'result': 'fake_data',
            'param1': param1,
            'param2': param2
        }
```

### 2. Add Tests in test_backend_endpoints.py

Create a new test class for the endpoint group:

```python
class TestNewFeature:
    """Test new feature endpoints."""
    
    def test_new_endpoint_happy_path(self, client, auth_headers):
        """Test successful response."""
        response = client.get(
            '/api/new/endpoint?param1=value1',
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'result' in data['data']
    
    def test_new_endpoint_requires_auth(self, client):
        """Test authentication requirement."""
        response = client.get('/api/new/endpoint')
        assert response.status_code == 401
    
    def test_new_endpoint_error_handling(self, client, auth_headers, fake_services):
        """Test error propagation."""
        service = list(fake_services.values())[0]
        service.set_should_fail(True)
        
        response = client.get('/api/new/endpoint', headers=auth_headers)
        assert response.status_code in [400, 500]
        data = response.get_json()
        assert data['success'] is False
```

### 3. Test Both Success and Error Paths

Always test:
- **Authentication**: Endpoint rejects requests without valid API key
- **Happy path**: Returns expected structure with fake data
- **Error handling**: Properly propagates service errors
- **Parameter validation**: Validates required parameters
- **Account handling**: Accepts account parameter if applicable

## FakeCoreService API

The `FakeCoreService` stub provides these methods:

### File Management
- `list_dir(path: str)` - Returns fake file list or error code
- `search_files(keyword: str, path: str)` - Returns fake search results

### Transfer Operations
- `get_transfer_status()` - Returns fake transfer status with counts
- `get_transfer_queue()` - Returns list of fake transfer tasks
- `export_transfer_results()` - Returns completed transfer tasks
- `clear_transfer_queue()` - Clears transfer queue

### Share Operations
- `get_share_status()` - Returns fake share status with counts
- `get_share_queue()` - Returns list of fake share tasks
- `export_share_results()` - Returns completed share tasks
- `clear_share_queue()` - Clears share queue

### Control Methods
- `set_should_fail(should_fail: bool)` - Control error behavior for testing

## Examples

### Testing Error States

```python
def test_endpoint_with_error(client, auth_headers, fake_services):
    # Configure service to return errors
    service = list(fake_services.values())[0]
    service.set_should_fail(True)
    
    response = client.get('/api/endpoint', headers=auth_headers)
    assert response.status_code == 400
    assert response.get_json()['success'] is False
```

### Testing Account Parameters

```python
def test_endpoint_with_account(client, auth_headers):
    response = client.get(
        '/api/endpoint?account=test_account2',
        headers=auth_headers
    )
    assert response.status_code == 200
```

### Testing POST Requests

```python
def test_post_endpoint(client, auth_headers):
    payload = {'param': 'value'}
    response = client.post(
        '/api/endpoint',
        json=payload,
        headers=auth_headers
    )
    assert response.status_code == 200
```

## Best Practices

1. **No Real Network Calls**: All tests use fakes - never make real Baidu API calls
2. **Deterministic Data**: FakeCoreService returns consistent data for reproducible tests
3. **Test Authentication**: Always verify auth is enforced correctly
4. **Test Errors**: Validate both success and error paths
5. **Clear Test Names**: Use descriptive test method names explaining what's being tested
6. **Isolate Tests**: Each test should be independent and not rely on others

## CI Integration

Integration tests run automatically in CI via:
```bash
pytest tests/integration
```

Add this to your CI helper scripts to ensure integration tests are included in the test suite.
