"""
Unit tests for SettingsManager module.
Tests settings persistence, validation, and error handling using temporary directories.
"""
import json
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from settings_manager import SettingsManager
from config import Config


class TestSettingsManagerDefaults:
    """Test default settings generation."""
    
    def test_get_default_settings_structure(self, tmp_path):
        """Default settings should have all required keys."""
        manager = SettingsManager(str(tmp_path))
        defaults = manager.get_default_settings()
        
        assert 'throttle' in defaults
        assert 'workers' in defaults
        assert 'rate_limit' in defaults
        assert 'ui' in defaults
        
    def test_get_default_throttle_settings(self, tmp_path):
        """Default throttle settings should match Config values."""
        manager = SettingsManager(str(tmp_path))
        defaults = manager.get_default_settings()
        throttle = defaults['throttle']
        
        assert throttle['jitter_ms_min'] == Config.THROTTLE_JITTER_MS_MIN
        assert throttle['jitter_ms_max'] == Config.THROTTLE_JITTER_MS_MAX
        assert throttle['ops_per_window'] == Config.THROTTLE_OPS_PER_WINDOW
        assert throttle['window_sec'] == Config.THROTTLE_WINDOW_SEC
        assert throttle['window_rest_sec'] == Config.THROTTLE_WINDOW_REST_SEC
        assert throttle['max_consecutive_failures'] == Config.THROTTLE_MAX_CONSECUTIVE_FAILURES
        assert throttle['pause_sec_on_failure'] == Config.THROTTLE_PAUSE_SEC_ON_FAILURE
        assert throttle['backoff_factor'] == Config.THROTTLE_BACKOFF_FACTOR
        assert throttle['cooldown_on_errno_-62_sec'] == Config.THROTTLE_COOLDOWN_ON_ERRNO_62_SEC
        
    def test_get_default_worker_settings(self, tmp_path):
        """Default worker settings should match Config values."""
        manager = SettingsManager(str(tmp_path))
        defaults = manager.get_default_settings()
        workers = defaults['workers']
        
        assert workers['max_transfer_workers'] == Config.MAX_TRANSFER_WORKERS
        assert workers['max_share_workers'] == Config.MAX_SHARE_WORKERS
        
    def test_get_default_ui_settings(self, tmp_path):
        """Default UI settings should have expected values."""
        manager = SettingsManager(str(tmp_path))
        defaults = manager.get_default_settings()
        ui = defaults['ui']
        
        assert ui['auto_refresh_interval'] == 5000
        assert ui['api_key_retention'] is True


class TestSettingsManagerLoad:
    """Test loading settings from file."""
    
    def test_load_missing_file_returns_defaults(self, tmp_path):
        """Loading when file doesn't exist should return defaults."""
        manager = SettingsManager(str(tmp_path))
        settings = manager.load()
        
        defaults = manager.get_default_settings()
        assert settings == defaults
        
    def test_load_valid_file(self, tmp_path):
        """Loading valid JSON file should return saved settings."""
        manager = SettingsManager(str(tmp_path))
        
        test_settings = {
            'throttle': {
                'jitter_ms_min': 1000,
                'jitter_ms_max': 2000,
                'ops_per_window': 30,
                'window_sec': 45,
                'window_rest_sec': 15,
                'max_consecutive_failures': 3,
                'pause_sec_on_failure': 90,
                'backoff_factor': 2.0,
                'cooldown_on_errno_-62_sec': 180
            },
            'workers': {
                'max_transfer_workers': 2,
                'max_share_workers': 3
            },
            'rate_limit': {
                'enabled': False
            },
            'ui': {
                'auto_refresh_interval': 3000,
                'api_key_retention': False
            }
        }
        
        # Write test settings
        settings_file = os.path.join(str(tmp_path), 'control_panel_settings.json')
        with open(settings_file, 'w') as f:
            json.dump(test_settings, f)
        
        loaded = manager.load()
        assert loaded['throttle']['jitter_ms_min'] == 1000
        assert loaded['workers']['max_transfer_workers'] == 2
        assert loaded['ui']['auto_refresh_interval'] == 3000
        
    def test_load_corrupted_file_returns_defaults(self, tmp_path):
        """Loading corrupted JSON should return defaults."""
        manager = SettingsManager(str(tmp_path))
        
        # Write invalid JSON
        settings_file = os.path.join(str(tmp_path), 'control_panel_settings.json')
        with open(settings_file, 'w') as f:
            f.write('{ invalid json content')
        
        loaded = manager.load()
        defaults = manager.get_default_settings()
        assert loaded == defaults
        
    def test_load_partial_settings_merges_with_defaults(self, tmp_path):
        """Loading partial settings should merge with defaults."""
        manager = SettingsManager(str(tmp_path))
        
        partial_settings = {
            'throttle': {
                'jitter_ms_min': 800
            },
            'workers': {
                'max_transfer_workers': 5
            }
        }
        
        settings_file = os.path.join(str(tmp_path), 'control_panel_settings.json')
        with open(settings_file, 'w') as f:
            json.dump(partial_settings, f)
        
        loaded = manager.load()
        
        # Partial values should be present
        assert loaded['throttle']['jitter_ms_min'] == 800
        assert loaded['workers']['max_transfer_workers'] == 5
        
        # Missing values should be defaults
        defaults = manager.get_default_settings()
        assert loaded['throttle']['jitter_ms_max'] == defaults['throttle']['jitter_ms_max']
        assert loaded['ui']['auto_refresh_interval'] == defaults['ui']['auto_refresh_interval']


class TestSettingsManagerSave:
    """Test saving settings to file."""
    
    def test_save_creates_file(self, tmp_path):
        """Saving should create the settings file."""
        manager = SettingsManager(str(tmp_path))
        settings = manager.get_default_settings()
        
        result = manager.save(settings)
        
        assert result is True
        settings_file = os.path.join(str(tmp_path), 'control_panel_settings.json')
        assert os.path.exists(settings_file)
        
    def test_save_writes_valid_json(self, tmp_path):
        """Saved file should contain valid JSON."""
        manager = SettingsManager(str(tmp_path))
        test_settings = {
            'throttle': {
                'jitter_ms_min': 1200,
                'jitter_ms_max': 1800,
                'ops_per_window': 40,
                'window_sec': 50,
                'window_rest_sec': 10,
                'max_consecutive_failures': 4,
                'pause_sec_on_failure': 80,
                'backoff_factor': 1.8,
                'cooldown_on_errno_-62_sec': 150
            },
            'workers': {
                'max_transfer_workers': 3,
                'max_share_workers': 2
            },
            'rate_limit': {
                'enabled': True
            },
            'ui': {
                'auto_refresh_interval': 4000,
                'api_key_retention': True
            }
        }
        
        manager.save(test_settings)
        
        settings_file = os.path.join(str(tmp_path), 'control_panel_settings.json')
        with open(settings_file, 'r') as f:
            loaded = json.load(f)
        
        assert loaded['throttle']['jitter_ms_min'] == 1200
        assert loaded['workers']['max_transfer_workers'] == 3
        
    def test_save_creates_data_dir_if_missing(self, tmp_path):
        """Saving should create data directory if it doesn't exist."""
        nonexistent_dir = os.path.join(str(tmp_path), 'nested', 'data', 'dir')
        manager = SettingsManager(nonexistent_dir)
        
        result = manager.save(manager.get_default_settings())
        
        assert result is True
        assert os.path.exists(nonexistent_dir)
        
    def test_save_handles_io_error(self, tmp_path):
        """Save should return False on IO error."""
        manager = SettingsManager(str(tmp_path))
        
        with patch('builtins.open', side_effect=IOError("Disk full")):
            result = manager.save(manager.get_default_settings())
        
        assert result is False
        
    def test_save_handles_type_error(self, tmp_path):
        """Save should return False on non-serializable data."""
        manager = SettingsManager(str(tmp_path))
        
        invalid_settings = {
            'throttle': {
                'function': lambda x: x  # Non-serializable
            }
        }
        
        result = manager.save(invalid_settings)
        assert result is False


class TestSettingsManagerUpdate:
    """Test updating settings."""
    
    def test_update_applies_partial_changes(self, tmp_path):
        """Update should apply partial changes and preserve existing settings."""
        manager = SettingsManager(str(tmp_path))
        
        # Save initial settings
        initial = manager.get_default_settings()
        manager.save(initial)
        
        # Update only throttle jitter
        updates = {
            'throttle': {
                'jitter_ms_min': 999
            }
        }
        
        result = manager.update(updates)
        
        assert result['throttle']['jitter_ms_min'] == 999
        # Other throttle settings should be preserved
        assert result['throttle']['ops_per_window'] == initial['throttle']['ops_per_window']
        # Other sections should be preserved
        assert result['workers'] == initial['workers']
        
    def test_update_persists_changes(self, tmp_path):
        """Update should persist changes to file."""
        manager = SettingsManager(str(tmp_path))
        
        updates = {
            'workers': {
                'max_transfer_workers': 7
            }
        }
        
        manager.update(updates)
        
        # Create new manager instance to load from file
        new_manager = SettingsManager(str(tmp_path))
        loaded = new_manager.load()
        
        assert loaded['workers']['max_transfer_workers'] == 7


class TestSettingsManagerMerge:
    """Test settings merging logic."""
    
    def test_merge_flat_dicts(self, tmp_path):
        """Merge should handle flat dictionaries."""
        manager = SettingsManager(str(tmp_path))
        
        base = {'a': 1, 'b': 2}
        updates = {'b': 3, 'c': 4}
        
        result = manager._merge_settings(base, updates)
        
        assert result == {'a': 1, 'b': 3, 'c': 4}
        
    def test_merge_nested_dicts(self, tmp_path):
        """Merge should recursively handle nested dictionaries."""
        manager = SettingsManager(str(tmp_path))
        
        base = {
            'throttle': {
                'jitter_ms_min': 500,
                'jitter_ms_max': 1500
            },
            'workers': {
                'max_transfer_workers': 1
            }
        }
        
        updates = {
            'throttle': {
                'jitter_ms_min': 800
            },
            'ui': {
                'auto_refresh_interval': 6000
            }
        }
        
        result = manager._merge_settings(base, updates)
        
        assert result['throttle']['jitter_ms_min'] == 800
        assert result['throttle']['jitter_ms_max'] == 1500  # Preserved
        assert result['workers']['max_transfer_workers'] == 1  # Preserved
        assert result['ui']['auto_refresh_interval'] == 6000  # Added
        
    def test_merge_replaces_non_dict_values(self, tmp_path):
        """Merge should replace non-dict values."""
        manager = SettingsManager(str(tmp_path))
        
        base = {'a': 1, 'b': {'nested': 2}}
        updates = {'a': 10, 'b': 'string'}
        
        result = manager._merge_settings(base, updates)
        
        assert result == {'a': 10, 'b': 'string'}


class TestSettingsManagerValidation:
    """Test settings validation."""
    
    def test_validate_throttle_valid_settings(self, tmp_path):
        """Valid throttle settings should pass validation."""
        manager = SettingsManager(str(tmp_path))
        
        valid_throttle = {
            'jitter_ms_min': 600,
            'jitter_ms_max': 1200,
            'ops_per_window': 40,
            'window_sec': 50,
            'window_rest_sec': 15,
            'max_consecutive_failures': 4,
            'pause_sec_on_failure': 70,
            'backoff_factor': 2.0,
            'cooldown_on_errno_-62_sec': 130
        }
        
        is_valid, error = manager.validate_throttle_settings(valid_throttle)
        
        assert is_valid is True
        assert error is None
        
    def test_validate_throttle_missing_field(self, tmp_path):
        """Missing required field should fail validation."""
        manager = SettingsManager(str(tmp_path))
        
        incomplete_throttle = {
            'jitter_ms_min': 600,
            'jitter_ms_max': 1200
            # Missing other required fields
        }
        
        is_valid, error = manager.validate_throttle_settings(incomplete_throttle)
        
        assert is_valid is False
        assert 'Missing required field' in error
        
    def test_validate_throttle_invalid_jitter_min(self, tmp_path):
        """Invalid jitter_ms_min should fail validation."""
        manager = SettingsManager(str(tmp_path))
        
        defaults = manager.get_default_settings()['throttle']
        
        # Test negative value
        invalid_throttle = defaults.copy()
        invalid_throttle['jitter_ms_min'] = -1
        is_valid, error = manager.validate_throttle_settings(invalid_throttle)
        assert is_valid is False
        assert 'jitter_ms_min' in error
        
        # Test too large value
        invalid_throttle['jitter_ms_min'] = 10001
        is_valid, error = manager.validate_throttle_settings(invalid_throttle)
        assert is_valid is False
        
    def test_validate_throttle_invalid_jitter_max(self, tmp_path):
        """Invalid jitter_ms_max should fail validation."""
        manager = SettingsManager(str(tmp_path))
        
        defaults = manager.get_default_settings()['throttle']
        
        # Test max < min
        invalid_throttle = defaults.copy()
        invalid_throttle['jitter_ms_min'] = 1000
        invalid_throttle['jitter_ms_max'] = 500
        is_valid, error = manager.validate_throttle_settings(invalid_throttle)
        assert is_valid is False
        assert 'jitter_ms_max' in error
        
    def test_validate_throttle_invalid_ops_per_window(self, tmp_path):
        """Invalid ops_per_window should fail validation."""
        manager = SettingsManager(str(tmp_path))
        
        defaults = manager.get_default_settings()['throttle']
        
        # Test zero
        invalid_throttle = defaults.copy()
        invalid_throttle['ops_per_window'] = 0
        is_valid, error = manager.validate_throttle_settings(invalid_throttle)
        assert is_valid is False
        
        # Test too large
        invalid_throttle['ops_per_window'] = 1001
        is_valid, error = manager.validate_throttle_settings(invalid_throttle)
        assert is_valid is False
        
    def test_validate_throttle_invalid_backoff_factor(self, tmp_path):
        """Invalid backoff_factor should fail validation."""
        manager = SettingsManager(str(tmp_path))
        
        defaults = manager.get_default_settings()['throttle']
        
        # Test too small
        invalid_throttle = defaults.copy()
        invalid_throttle['backoff_factor'] = 0.5
        is_valid, error = manager.validate_throttle_settings(invalid_throttle)
        assert is_valid is False
        
        # Test too large
        invalid_throttle['backoff_factor'] = 6.0
        is_valid, error = manager.validate_throttle_settings(invalid_throttle)
        assert is_valid is False
        
    def test_validate_worker_valid_settings(self, tmp_path):
        """Valid worker settings should pass validation."""
        manager = SettingsManager(str(tmp_path))
        
        valid_workers = {
            'max_transfer_workers': 3,
            'max_share_workers': 2
        }
        
        is_valid, error = manager.validate_worker_settings(valid_workers)
        
        assert is_valid is True
        assert error is None
        
    def test_validate_worker_invalid_transfer_workers(self, tmp_path):
        """Invalid max_transfer_workers should fail validation."""
        manager = SettingsManager(str(tmp_path))
        
        # Test zero
        invalid_workers = {'max_transfer_workers': 0}
        is_valid, error = manager.validate_worker_settings(invalid_workers)
        assert is_valid is False
        
        # Test too large
        invalid_workers = {'max_transfer_workers': 11}
        is_valid, error = manager.validate_worker_settings(invalid_workers)
        assert is_valid is False
        
    def test_validate_worker_invalid_share_workers(self, tmp_path):
        """Invalid max_share_workers should fail validation."""
        manager = SettingsManager(str(tmp_path))
        
        # Test zero
        invalid_workers = {'max_share_workers': 0}
        is_valid, error = manager.validate_worker_settings(invalid_workers)
        assert is_valid is False
        
        # Test too large
        invalid_workers = {'max_share_workers': 11}
        is_valid, error = manager.validate_worker_settings(invalid_workers)
        assert is_valid is False
        
    def test_validate_worker_partial_settings(self, tmp_path):
        """Partial worker settings should validate successfully."""
        manager = SettingsManager(str(tmp_path))
        
        # Only transfer workers
        workers = {'max_transfer_workers': 5}
        is_valid, error = manager.validate_worker_settings(workers)
        assert is_valid is True
        
        # Only share workers
        workers = {'max_share_workers': 4}
        is_valid, error = manager.validate_worker_settings(workers)
        assert is_valid is True


class TestSettingsManagerEdgeCases:
    """Test edge cases and error scenarios."""
    
    def test_manager_with_default_data_dir(self):
        """Manager should use Config.DATA_DIR when no path provided."""
        manager = SettingsManager()
        assert manager.data_dir == Config.DATA_DIR
        
    def test_load_with_permission_error(self, tmp_path):
        """Load should return defaults on permission error."""
        manager = SettingsManager(str(tmp_path))
        
        with patch('builtins.open', side_effect=IOError("Permission denied")):
            loaded = manager.load()
        
        defaults = manager.get_default_settings()
        assert loaded == defaults
        
    def test_ensure_data_dir_creates_directory(self, tmp_path):
        """_ensure_data_dir should create directory if missing."""
        nested_path = os.path.join(str(tmp_path), 'a', 'b', 'c')
        manager = SettingsManager(nested_path)
        
        assert os.path.exists(nested_path)
