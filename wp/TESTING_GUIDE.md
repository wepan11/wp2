# Testing Guide

## Overview

This project includes two test suites:
1. **Unit Tests** - Fast, isolated tests for individual components
2. **Integration Tests** - End-to-end tests for API endpoints

## Quick Start

### Run All Unit Tests
```bash
./run_unit_tests.sh
```

### Run All Integration Tests
```bash
PYTHONPATH=$(pwd) /usr/bin/python3 -c "
import sys
sys.path.insert(0, '.venv/lib/python3.12/site-packages')
import pytest
pytest.main(['tests/integration/', '-v'])
"
```

### Run All Tests
```bash
PYTHONPATH=$(pwd) /usr/bin/python3 -c "
import sys
sys.path.insert(0, '.venv/lib/python3.12/site-packages')
import pytest
pytest.main(['tests/', '-v'])
"
```

## Unit Tests

### Location
- `tests/unit/`

### Coverage
- **Settings Manager** (48 tests)
  - Settings persistence (save/load/update)
  - Validation (throttle, worker configs)
  - Error handling (corrupted files, permissions)
  
- **Core Service Throttle** (16 tests)
  - Throttler initialization
  - Config updates
  - Worker synchronization
  - Behavior (success/failure handling)
  
- **Control Panel Helpers** (29 tests)
  - Queue aggregation
  - Health status
  - Account list building
  - Overview data assembly

### Running Unit Tests

```bash
# All unit tests
./run_unit_tests.sh

# Specific module
pytest tests/unit/test_settings_manager.py -v

# Specific test class
pytest tests/unit/test_settings_manager.py::TestSettingsManagerDefaults -v

# Specific test
pytest tests/unit/test_settings_manager.py::TestSettingsManagerDefaults::test_get_default_settings_structure -v

# With coverage
pytest tests/unit/ --cov=. --cov-report=term
```

### Characteristics
- ⚡ **Fast**: ~0.16s for all 76 tests
- 🔒 **Isolated**: No external dependencies
- 🎯 **Focused**: One behavior per test
- 🔄 **Repeatable**: Deterministic results

## Integration Tests

### Location
- `tests/integration/`

### Coverage
- Health and info endpoints
- File operations (list, search)
- Transfer operations (status, queue, control)
- Share operations (status, queue, control)
- Settings endpoints (GET/PUT)
- Control queues aggregation
- Authentication flows

### Running Integration Tests

```bash
# All integration tests
PYTHONPATH=$(pwd) /usr/bin/python3 -c "
import sys
sys.path.insert(0, '.venv/lib/python3.12/site-packages')
import pytest
pytest.main(['tests/integration/', '-v'])
"

# Specific test class
pytest tests/integration/test_backend_endpoints.py::TestHealthAndInfo -v
```

### Characteristics
- 🌐 **End-to-end**: Full request/response cycle
- 🔌 **Mocked**: Uses FakeCoreService (no real API calls)
- 📋 **Comprehensive**: All API endpoints covered

## Test Fixtures

### Unit Test Fixtures

**tmp_path** (from tests/conftest.py)
```python
def test_with_temp_dir(tmp_path):
    # tmp_path is a temporary directory
    file_path = os.path.join(str(tmp_path), 'test.json')
    # Directory is automatically cleaned up
```

**clean_env** (from tests/conftest.py)
```python
def test_with_clean_env(clean_env, monkeypatch):
    # Monkeypatch environment without affecting system
    monkeypatch.setenv('KEY', 'value')
```

### Integration Test Fixtures

**app_with_fakes** (from tests/integration/conftest.py)
- Flask test app with mocked services

**client** (from tests/integration/conftest.py)
- Flask test client

**api_key** (from tests/integration/conftest.py)
- Valid API key for testing

**auth_headers** (from tests/integration/conftest.py)
- Headers with authentication

## Writing New Tests

### Unit Test Template

```python
"""
Unit tests for MyModule.
Tests core functionality with mocked dependencies.
"""
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from my_module import MyClass


class TestMyClass:
    """Test MyClass functionality."""
    
    def test_basic_operation(self, tmp_path):
        """Test basic operation with temp directory."""
        instance = MyClass(str(tmp_path))
        result = instance.do_something()
        
        assert result is not None
        assert result['status'] == 'success'
        
    def test_error_handling(self):
        """Test error handling."""
        instance = MyClass()
        
        with patch('builtins.open', side_effect=IOError("Error")):
            result = instance.load_file()
            
        assert result is None
```

### Integration Test Template

```python
def test_new_endpoint(client, auth_headers):
    """Test new endpoint with authentication."""
    response = client.get('/api/new-endpoint', headers=auth_headers)
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'result' in data
```

## Best Practices

### Unit Tests
1. **Test one thing** - Each test validates one behavior
2. **Use descriptive names** - `test_load_missing_file_returns_defaults`
3. **Mock external dependencies** - No real I/O, network, or DB
4. **Use fixtures** - Share setup code via pytest fixtures
5. **Test edge cases** - Empty inputs, errors, boundaries

### Integration Tests
1. **Test user flows** - End-to-end scenarios
2. **Use fake services** - Mock external APIs
3. **Validate responses** - Check status codes and structure
4. **Test auth flows** - Both authenticated and unauthenticated

### All Tests
1. **Keep tests fast** - Avoid sleeps and slow operations
2. **Make tests deterministic** - No randomness
3. **Clean up after tests** - Use fixtures with cleanup
4. **Document test intent** - Clear docstrings
5. **Run tests before commit** - Ensure nothing breaks

## Continuous Integration

### Pre-commit Checks
```bash
# Run all tests
./run_unit_tests.sh && pytest tests/integration/ -v

# Check for failures
echo $?  # Should be 0
```

### Coverage Goals
- Unit tests: Focus on new modules (control panel helpers)
- Integration tests: All API endpoints
- Overall: Aim for >80% coverage on critical paths

## Troubleshooting

### Import Errors
```bash
# Ensure PYTHONPATH is set
export PYTHONPATH=$(pwd)

# Ensure venv site-packages in path
export PYTHONPATH=$PYTHONPATH:.venv/lib/python3.12/site-packages
```

### Pytest Not Found
```bash
# Install pytest
sudo apt-get install python3-pytest
```

### Tests Hang
- Check for blocking I/O operations
- Verify mocks are properly configured
- Look for infinite loops in test code

### Flaky Tests
- Remove time.sleep() calls
- Mock time-dependent operations
- Ensure no shared state between tests

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [unittest.mock Guide](https://docs.python.org/3/library/unittest.mock.html)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)

## Summary

| Test Suite | Tests | Duration | Purpose |
|------------|-------|----------|---------|
| Unit | 76 | ~0.16s | Component testing |
| Integration | 38 | ~2.2s | API endpoint testing |
| **Total** | **114** | **~2.4s** | **Full coverage** |

Run tests frequently during development to catch issues early!
