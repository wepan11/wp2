"""
Settings Manager Module

Handles persistence of control panel runtime settings to JSON file.
Settings include throttle configuration, worker counts, UI preferences, etc.
"""
import os
import json
from typing import Dict, Any, Optional
from config import Config


class SettingsManager:
    """Manages control panel settings persistence."""
    
    def __init__(self, data_dir: str = None):
        """
        Initialize settings manager.
        
        Args:
            data_dir: Directory to store settings file. Defaults to Config.DATA_DIR
        """
        self.data_dir = data_dir or Config.DATA_DIR
        self.settings_file = os.path.join(self.data_dir, 'control_panel_settings.json')
        self._ensure_data_dir()
    
    def _ensure_data_dir(self):
        """Ensure data directory exists."""
        os.makedirs(self.data_dir, exist_ok=True)
    
    def get_default_settings(self) -> Dict[str, Any]:
        """
        Get default settings structure.
        
        Returns:
            Dictionary with default settings values
        """
        return {
            'throttle': {
                'jitter_ms_min': Config.THROTTLE_JITTER_MS_MIN,
                'jitter_ms_max': Config.THROTTLE_JITTER_MS_MAX,
                'ops_per_window': Config.THROTTLE_OPS_PER_WINDOW,
                'window_sec': Config.THROTTLE_WINDOW_SEC,
                'window_rest_sec': Config.THROTTLE_WINDOW_REST_SEC,
                'max_consecutive_failures': Config.THROTTLE_MAX_CONSECUTIVE_FAILURES,
                'pause_sec_on_failure': Config.THROTTLE_PAUSE_SEC_ON_FAILURE,
                'backoff_factor': Config.THROTTLE_BACKOFF_FACTOR,
                'cooldown_on_errno_-62_sec': Config.THROTTLE_COOLDOWN_ON_ERRNO_62_SEC
            },
            'workers': {
                'max_transfer_workers': Config.MAX_TRANSFER_WORKERS,
                'max_share_workers': Config.MAX_SHARE_WORKERS
            },
            'rate_limit': {
                'enabled': Config.RATE_LIMIT_ENABLED
            },
            'ui': {
                'auto_refresh_interval': 5000,  # milliseconds
                'api_key_retention': True  # whether to persist API key in localStorage
            }
        }
    
    def load(self) -> Dict[str, Any]:
        """
        Load settings from JSON file.
        
        Returns:
            Settings dictionary. Returns defaults if file doesn't exist or is invalid.
        """
        if not os.path.exists(self.settings_file):
            return self.get_default_settings()
        
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                saved_settings = json.load(f)
            
            # Merge with defaults to ensure all keys exist
            defaults = self.get_default_settings()
            merged = self._merge_settings(defaults, saved_settings)
            return merged
        
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Failed to load settings from {self.settings_file}: {e}")
            return self.get_default_settings()
    
    def save(self, settings: Dict[str, Any]) -> bool:
        """
        Save settings to JSON file.
        
        Args:
            settings: Settings dictionary to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self._ensure_data_dir()
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            return True
        except (IOError, TypeError) as e:
            print(f"Error: Failed to save settings to {self.settings_file}: {e}")
            return False
    
    def update(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update specific settings and save.
        
        Args:
            updates: Partial settings to update
            
        Returns:
            Updated full settings dictionary
        """
        current = self.load()
        updated = self._merge_settings(current, updates)
        self.save(updated)
        return updated
    
    def _merge_settings(self, base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge two settings dictionaries.
        
        Args:
            base: Base settings dictionary
            updates: Updates to apply
            
        Returns:
            Merged dictionary
        """
        result = base.copy()
        
        for key, value in updates.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_settings(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def validate_throttle_settings(self, throttle: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate throttle settings.
        
        Args:
            throttle: Throttle settings dictionary
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check required fields
            required_fields = [
                'jitter_ms_min', 'jitter_ms_max', 'ops_per_window',
                'window_sec', 'window_rest_sec', 'max_consecutive_failures',
                'pause_sec_on_failure', 'backoff_factor', 'cooldown_on_errno_-62_sec'
            ]
            
            for field in required_fields:
                if field not in throttle:
                    return False, f"Missing required field: {field}"
            
            # Validate ranges
            if throttle['jitter_ms_min'] < 0 or throttle['jitter_ms_min'] > 10000:
                return False, "jitter_ms_min must be between 0 and 10000"
            
            if throttle['jitter_ms_max'] < throttle['jitter_ms_min'] or throttle['jitter_ms_max'] > 10000:
                return False, "jitter_ms_max must be between jitter_ms_min and 10000"
            
            if throttle['ops_per_window'] < 1 or throttle['ops_per_window'] > 1000:
                return False, "ops_per_window must be between 1 and 1000"
            
            if throttle['window_sec'] < 1 or throttle['window_sec'] > 3600:
                return False, "window_sec must be between 1 and 3600"
            
            if throttle['window_rest_sec'] < 0 or throttle['window_rest_sec'] > 600:
                return False, "window_rest_sec must be between 0 and 600"
            
            if throttle['max_consecutive_failures'] < 1 or throttle['max_consecutive_failures'] > 100:
                return False, "max_consecutive_failures must be between 1 and 100"
            
            if throttle['pause_sec_on_failure'] < 0 or throttle['pause_sec_on_failure'] > 3600:
                return False, "pause_sec_on_failure must be between 0 and 3600"
            
            if throttle['backoff_factor'] < 1.0 or throttle['backoff_factor'] > 5.0:
                return False, "backoff_factor must be between 1.0 and 5.0"
            
            if throttle['cooldown_on_errno_-62_sec'] < 0 or throttle['cooldown_on_errno_-62_sec'] > 3600:
                return False, "cooldown_on_errno_-62_sec must be between 0 and 3600"
            
            return True, None
            
        except (KeyError, TypeError, ValueError) as e:
            return False, f"Invalid throttle settings: {str(e)}"
    
    def validate_worker_settings(self, workers: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate worker settings.
        
        Args:
            workers: Worker settings dictionary
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if 'max_transfer_workers' in workers:
                if workers['max_transfer_workers'] < 1 or workers['max_transfer_workers'] > 10:
                    return False, "max_transfer_workers must be between 1 and 10"
            
            if 'max_share_workers' in workers:
                if workers['max_share_workers'] < 1 or workers['max_share_workers'] > 10:
                    return False, "max_share_workers must be between 1 and 10"
            
            return True, None
            
        except (KeyError, TypeError, ValueError) as e:
            return False, f"Invalid worker settings: {str(e)}"
