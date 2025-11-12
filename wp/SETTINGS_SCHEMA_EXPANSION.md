# Settings Schema Expansion - Implementation Summary

## Overview
Expanded the control panel settings schema to include global constraints for share defaults and transfer defaults, enabling user-configured defaults for all Baidu interactions.

## Changes Implemented

### 1. Settings Manager Enhancements (`settings_manager.py`)

#### New Default Settings Sections
- **`share_defaults`**:
  - `expiry`: Default share expiry (0=永久, 1=1天, 7=7天, 30=30天)
  - `auto_password`: Toggle for automatic random password generation
  - `fixed_password`: Optional fixed 4-character password (empty string if using auto)

- **`transfer_defaults`**:
  - `target_path`: Default target directory for transfer operations

#### New Validation Methods
- `validate_share_defaults()`: Validates expiry values (0,1,7,30) and password format (empty or 4 chars)
- `validate_transfer_defaults()`: Validates target_path is non-empty and starts with `/`

#### Backward Compatibility
- Old settings files without new sections automatically merge with defaults
- No breaking changes to existing settings structure

### 2. Core Service Integration (`core_service.py`)

#### Instance Variables
- Added `share_defaults` dict to store configured share settings
- Added `transfer_defaults` dict to store configured transfer settings
- Initialized with sensible defaults on service creation

#### New Method: `apply_settings(settings)`
- Accepts full settings bundle from SettingsManager
- Applies throttle configuration via existing `update_throttle()` method
- Stores share_defaults and transfer_defaults for use by workers
- Logs all configuration updates

### 3. Server Wiring (`server.py`)

#### Global State
- Added `current_settings` cache to store loaded settings
- Initialized in `initialize_app()` via SettingsManager

#### Service Creation Updates
- `get_or_create_service()` now:
  - Passes full settings bundle to new CoreService instances
  - Calls `apply_settings()` on newly created services
  - Ensures services use persisted configuration immediately

#### Settings Endpoint Enhancements
- **GET `/api/control/settings`**:
  - Returns new sections (`share_defaults`, `transfer_defaults`) with defaults
  
- **PUT/PATCH `/api/control/settings`**:
  - Validates new sections using new validation methods
  - Applies settings to all active CoreService instances via `apply_settings()`
  - Syncs throttle config back to global Config for future services
  - Clamps worker counts to 1 (respecting single-thread requirement)
  - Updates cached `current_settings`

### 4. Test Coverage

#### Unit Tests (`tests/unit/test_settings_manager.py`)
Added 14 new test classes/methods:
- `TestShareDefaultsValidation`: 6 tests for share defaults validation
- `TestTransferDefaultsValidation`: 4 tests for transfer defaults validation
- `TestNewSettingsPersistence`: 4 tests for persistence and backward compatibility

**Total unit tests: 90 (all passing)**

#### Integration Tests (`tests/integration/test_backend_endpoints.py`)
Added 8 new test methods to `TestSettingsEndpoints`:
- `test_get_settings_includes_new_sections`: Verifies API returns new sections
- `test_update_settings_valid_share_defaults`: Valid share config accepted
- `test_update_settings_invalid_share_expiry`: Invalid expiry rejected
- `test_update_settings_invalid_share_password`: Invalid password length rejected
- `test_update_settings_valid_transfer_defaults`: Valid transfer config accepted
- `test_update_settings_invalid_transfer_path`: Invalid path rejected
- `test_update_settings_applies_to_services`: Settings applied to active services
- Updated `test_update_settings_empty_body`: Empty JSON body properly rejected

**Total integration tests: 45 (all passing)**

#### Fake Service Updates (`tests/integration/conftest.py`)
- Extended `FakeCoreService` with `apply_settings()` stub for testing

## API Response Examples

### GET /api/control/settings
```json
{
  "success": true,
  "data": {
    "throttle": { ... },
    "workers": { ... },
    "rate_limit": { ... },
    "ui": { ... },
    "share_defaults": {
      "expiry": 7,
      "auto_password": true,
      "fixed_password": ""
    },
    "transfer_defaults": {
      "target_path": "/批量转存"
    },
    "accounts": ["main", "backup"],
    "default_account": "main"
  }
}
```

### PUT /api/control/settings
```json
{
  "share_defaults": {
    "expiry": 30,
    "auto_password": false,
    "fixed_password": "ab12"
  },
  "transfer_defaults": {
    "target_path": "/custom/target"
  }
}
```

## Validation Rules

### Share Defaults
- **expiry**: Must be one of [0, 1, 7, 30]
- **auto_password**: Must be boolean
- **fixed_password**: Must be empty string or exactly 4 characters

### Transfer Defaults
- **target_path**: Must be non-empty string starting with `/`

## Persistence

Settings are stored in `data/control_panel_settings.json` with the following structure:
```json
{
  "throttle": { ... },
  "workers": { ... },
  "rate_limit": { ... },
  "ui": { ... },
  "share_defaults": {
    "expiry": 7,
    "auto_password": true,
    "fixed_password": ""
  },
  "transfer_defaults": {
    "target_path": "/批量转存"
  }
}
```

## Future Work (Out of Scope)

This ticket focused on **schema expansion and persistence**. Future tickets should:
1. Update worker logic to **use** stored share_defaults when creating share tasks
2. Update worker logic to **use** stored transfer_defaults when creating transfer tasks
3. Build frontend UI for editing these settings
4. Add task-level overrides that can supersede defaults

## Testing Summary

- ✅ All 90 unit tests pass (14 new tests for schema expansion)
- ✅ All 45 integration tests pass (8 new tests for API endpoints)
- ✅ Backward compatibility verified (old settings files merge cleanly)
- ✅ Validation rules thoroughly tested (valid/invalid cases)
- ✅ Persistence verified (save/load cycle works correctly)
- ✅ Service integration verified (apply_settings propagates to services)

## Acceptance Criteria Met

✅ Newly saved share/transfer default values persist to `data/control_panel_settings.json`  
✅ Values returned by GET `/api/control/settings` endpoint  
✅ New CoreService instances inherit persisted settings without server restart  
✅ Validation errors surface with helpful messages  
✅ Unit & integration tests pass  
✅ Backward compatibility maintained (old settings files work)  
✅ Worker counts clamped to 1 for single-thread requirement  

## Files Modified

1. `settings_manager.py`: Added new sections, validation methods
2. `core_service.py`: Added apply_settings() method, default storage
3. `server.py`: Updated initialization, service creation, settings endpoints
4. `tests/unit/test_settings_manager.py`: Added 14 new tests
5. `tests/integration/test_backend_endpoints.py`: Added 8 new tests
6. `tests/integration/conftest.py`: Extended FakeCoreService

## Dependencies

This implementation provides the **foundation** for future tickets that will:
- Use share defaults in share task creation
- Use transfer defaults in transfer task creation
- Provide UI controls for editing these settings
