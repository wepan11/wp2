# Unit Tests for Control Panel Backend

This directory contains isolated unit tests for control panel backend components.

## Test Modules

### test_settings_manager.py
Tests for `SettingsManager` class that handles persistence of control panel settings.

**Coverage:**
- Default settings generation
- Loading from file (missing, valid, corrupted JSON)
- Saving settings with error handling
- Partial updates and merging
- Validation of throttle and worker settings
- Edge cases (permissions, missing directories)

**Test Classes:**
- `TestSettingsManagerDefaults` - Default settings structure
- `TestSettingsManagerLoad` - File loading and merging
- `TestSettingsManagerSave` - File saving and error handling
- `TestSettingsManagerUpdate` - Partial updates
- `TestSettingsManagerMerge` - Settings merging logic
- `TestSettingsManagerValidation` - Input validation
- `TestSettingsManagerEdgeCases` - Error scenarios

### test_core_service_throttle.py
Tests for `CoreService.update_throttle()` method and `Throttler` class.

**Coverage:**
- Throttler initialization with various configs
- Throttle config updates and propagation
- Worker state synchronization
- Throttler runtime behavior (success/failure handling)
- Edge cases (no workers, stopped workers)

**Test Classes:**
- `TestThrottlerInitialization` - Throttler setup
- `TestCoreServiceUpdateThrottle` - Throttle updates
- `TestThrottlerBehavior` - Runtime behavior
- `TestCoreServiceIntegration` - Integration scenarios

### test_control_panel_helpers.py
Tests for helper functions in `control_panel_helpers.py` module.

**Coverage:**
- Queue aggregation across multiple services
- Health status generation
- Account list building
- Overview data assembly
- Queue filtering and counting utilities

**Test Classes:**
- `TestAggregateQueueSummary` - Queue aggregation
- `TestBuildHealthStatus` - Health status generation
- `TestBuildAccountList` - Account list building
- `TestAggregateAccountQueues` - Per-account queue data
- `TestBuildOverviewData` - Complete overview assembly
- `TestFilterQueueByStatus` - Queue filtering utilities
- `TestCountTasksByStatus` - Task counting utilities

## Running Tests

### Using pytest (recommended)

```bash
# Run all unit tests with verbose output
PYTHONPATH=/home/engine/project/wp /usr/bin/python3 -c "import sys; sys.path.insert(0, '.venv/lib/python3.12/site-packages'); import pytest; pytest.main(['tests/unit/', '-v'])"

# Run specific test module
PYTHONPATH=/home/engine/project/wp /usr/bin/python3 -c "import sys; sys.path.insert(0, '.venv/lib/python3.12/site-packages'); import pytest; pytest.main(['tests/unit/test_settings_manager.py', '-v'])"

# Run with coverage
PYTHONPATH=/home/engine/project/wp /usr/bin/python3 -c "import sys; sys.path.insert(0, '.venv/lib/python3.12/site-packages'); import pytest; pytest.main(['tests/unit/', '-v', '--cov=.', '--cov-report=term'])"
```

### Simple runner script

```bash
# Create a simple runner
cd /home/engine/project/wp
./run_unit_tests.sh
```

## Test Isolation

These tests are designed to be fully isolated:
- Use `tmp_path` fixtures for file operations (no touching real data directory)
- Mock external dependencies (BaiduPanAdapter, file I/O)
- No shared state between tests
- Each test can run independently

## Design Principles

1. **Deterministic** - Tests produce same results every run
2. **Fast** - No network calls or slow operations
3. **Focused** - Each test validates one specific behavior
4. **Readable** - Clear test names and assertions
5. **Maintainable** - Easy to update when code changes

## Adding New Tests

When adding new control panel features:

1. Extract business logic into testable functions (see `control_panel_helpers.py`)
2. Create corresponding test class with descriptive name
3. Test happy path, edge cases, and error scenarios
4. Use mocks to isolate dependencies
5. Use fixtures for shared test setup
