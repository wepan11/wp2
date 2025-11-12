"""
Unit tests for CoreService throttle update functionality.
Tests throttle configuration updates and worker state synchronization.
"""
import os
import sys
import threading
import time
from unittest.mock import MagicMock, Mock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core_service import CoreService, Throttler, TransferWorker, ShareWorker


class FakeWorker(threading.Thread):
    """Fake worker thread for testing throttler updates."""
    
    def __init__(self, throttler):
        super().__init__(daemon=True)
        self.throttler = throttler
        self.is_running = True
        self._started = False
        
    def run(self):
        """Simulate worker running."""
        self._started = True
        while self.is_running:
            time.sleep(0.01)
            
    def is_alive(self):
        """Override to simulate running state."""
        return self._started and self.is_running
        
    def stop(self):
        """Stop the worker."""
        self.is_running = False


class TestThrottlerInitialization:
    """Test Throttler initialization and configuration."""
    
    def test_throttler_default_values(self):
        """Throttler should initialize with config values."""
        config = {
            'throttle': {
                'jitter_ms_min': 500,
                'jitter_ms_max': 1500,
                'ops_per_window': 50,
                'window_sec': 60,
                'window_rest_sec': 20,
                'max_consecutive_failures': 5,
                'pause_sec_on_failure': 60,
                'backoff_factor': 1.5,
                'cooldown_on_errno_-62_sec': 120
            }
        }
        
        throttler = Throttler(config)
        
        assert throttler.jitter_min == 500
        assert throttler.jitter_max == 1500
        assert throttler.ops_per_window == 50
        assert throttler.window_sec == 60
        assert throttler.window_rest_sec == 20
        assert throttler.max_consec_fail == 5
        assert throttler.pause_sec_on_failure == 60
        assert throttler.backoff_factor == 1.5
        assert throttler.cooldown_on_62 == 120
        
    def test_throttler_custom_values(self):
        """Throttler should use custom config values."""
        config = {
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
            }
        }
        
        throttler = Throttler(config)
        
        assert throttler.jitter_min == 1000
        assert throttler.jitter_max == 2000
        assert throttler.ops_per_window == 30
        assert throttler.window_sec == 45
        
    def test_throttler_missing_config(self):
        """Throttler should handle missing throttle config gracefully."""
        config = {}
        throttler = Throttler(config)
        
        # Should use defaults (0 or fallback values)
        assert throttler.ops_in_window == 0
        assert throttler.consec_fail == 0
        
    def test_throttler_initial_state(self):
        """Throttler should initialize tracking state."""
        config = {'throttle': {}}
        throttler = Throttler(config)
        
        assert throttler.ops_in_window == 0
        assert throttler.consec_fail == 0
        assert isinstance(throttler.window_start, float)


class TestCoreServiceUpdateThrottle:
    """Test CoreService.update_throttle() method."""
    
    def test_update_throttle_replaces_throttler(self):
        """update_throttle should create new Throttler instance."""
        initial_config = {
            'throttle': {
                'jitter_ms_min': 500,
                'jitter_ms_max': 1500,
                'ops_per_window': 50,
                'window_sec': 60,
                'window_rest_sec': 20,
                'max_consecutive_failures': 5,
                'pause_sec_on_failure': 60,
                'backoff_factor': 1.5,
                'cooldown_on_errno_-62_sec': 120
            }
        }
        
        # Create service with mocked adapter
        with patch('core_service.BaiduPanAdapter'):
            service = CoreService(cookie='fake_cookie', config=initial_config)
            initial_throttler = service.throttler
            
            # Update throttle config
            new_throttle_config = {
                'jitter_ms_min': 1000,
                'jitter_ms_max': 2000,
                'ops_per_window': 30,
                'window_sec': 45,
                'window_rest_sec': 15,
                'max_consecutive_failures': 3,
                'pause_sec_on_failure': 90,
                'backoff_factor': 2.0,
                'cooldown_on_errno_-62_sec': 180
            }
            
            service.update_throttle(new_throttle_config)
            
            # Throttler should be replaced
            assert service.throttler is not initial_throttler
            assert service.throttler.jitter_min == 1000
            assert service.throttler.ops_per_window == 30
            
    def test_update_throttle_updates_running_transfer_worker(self):
        """update_throttle should update running transfer worker's throttler."""
        config = {
            'throttle': {
                'jitter_ms_min': 500,
                'jitter_ms_max': 1500,
                'ops_per_window': 50,
                'window_sec': 60,
                'window_rest_sec': 20,
                'max_consecutive_failures': 5,
                'pause_sec_on_failure': 60,
                'backoff_factor': 1.5,
                'cooldown_on_errno_-62_sec': 120
            }
        }
        
        with patch('core_service.BaiduPanAdapter'):
            service = CoreService(cookie='fake_cookie', config=config)
            initial_throttler = service.throttler
            
            # Create fake running transfer worker
            fake_worker = FakeWorker(initial_throttler)
            service.transfer_worker = fake_worker
            fake_worker._started = True  # Simulate running state
            
            # Update throttle
            new_throttle_config = {
                'jitter_ms_min': 800,
                'jitter_ms_max': 1800,
                'ops_per_window': 40,
                'window_sec': 50,
                'window_rest_sec': 10,
                'max_consecutive_failures': 4,
                'pause_sec_on_failure': 70,
                'backoff_factor': 1.8,
                'cooldown_on_errno_-62_sec': 150
            }
            
            service.update_throttle(new_throttle_config)
            
            # Worker should have new throttler reference
            assert fake_worker.throttler is service.throttler
            assert fake_worker.throttler.jitter_min == 800
            
            # Cleanup
            fake_worker.stop()
            
    def test_update_throttle_updates_running_share_worker(self):
        """update_throttle should update running share worker's throttler."""
        config = {
            'throttle': {
                'jitter_ms_min': 500,
                'jitter_ms_max': 1500,
                'ops_per_window': 50,
                'window_sec': 60,
                'window_rest_sec': 20,
                'max_consecutive_failures': 5,
                'pause_sec_on_failure': 60,
                'backoff_factor': 1.5,
                'cooldown_on_errno_-62_sec': 120
            }
        }
        
        with patch('core_service.BaiduPanAdapter'):
            service = CoreService(cookie='fake_cookie', config=config)
            initial_throttler = service.throttler
            
            # Create fake running share worker
            fake_worker = FakeWorker(initial_throttler)
            service.share_worker = fake_worker
            fake_worker._started = True  # Simulate running state
            
            # Update throttle
            new_throttle_config = {
                'jitter_ms_min': 700,
                'jitter_ms_max': 1700,
                'ops_per_window': 35,
                'window_sec': 55,
                'window_rest_sec': 12,
                'max_consecutive_failures': 6,
                'pause_sec_on_failure': 75,
                'backoff_factor': 1.7,
                'cooldown_on_errno_-62_sec': 140
            }
            
            service.update_throttle(new_throttle_config)
            
            # Worker should have new throttler reference
            assert fake_worker.throttler is service.throttler
            assert fake_worker.throttler.jitter_min == 700
            
            # Cleanup
            fake_worker.stop()
            
    def test_update_throttle_updates_both_workers(self):
        """update_throttle should update both workers when running."""
        config = {
            'throttle': {
                'jitter_ms_min': 500,
                'jitter_ms_max': 1500,
                'ops_per_window': 50,
                'window_sec': 60,
                'window_rest_sec': 20,
                'max_consecutive_failures': 5,
                'pause_sec_on_failure': 60,
                'backoff_factor': 1.5,
                'cooldown_on_errno_-62_sec': 120
            }
        }
        
        with patch('core_service.BaiduPanAdapter'):
            service = CoreService(cookie='fake_cookie', config=config)
            initial_throttler = service.throttler
            
            # Create fake running workers
            transfer_worker = FakeWorker(initial_throttler)
            share_worker = FakeWorker(initial_throttler)
            
            service.transfer_worker = transfer_worker
            service.share_worker = share_worker
            
            transfer_worker._started = True
            share_worker._started = True
            
            # Update throttle
            new_throttle_config = {
                'jitter_ms_min': 600,
                'jitter_ms_max': 1600,
                'ops_per_window': 45,
                'window_sec': 65,
                'window_rest_sec': 18,
                'max_consecutive_failures': 7,
                'pause_sec_on_failure': 80,
                'backoff_factor': 1.6,
                'cooldown_on_errno_-62_sec': 160
            }
            
            service.update_throttle(new_throttle_config)
            
            # Both workers should have new throttler
            assert transfer_worker.throttler is service.throttler
            assert share_worker.throttler is service.throttler
            assert transfer_worker.throttler.jitter_min == 600
            assert share_worker.throttler.jitter_min == 600
            
            # Cleanup
            transfer_worker.stop()
            share_worker.stop()
            
    def test_update_throttle_no_running_workers(self):
        """update_throttle should work when no workers are running."""
        config = {
            'throttle': {
                'jitter_ms_min': 500,
                'jitter_ms_max': 1500,
                'ops_per_window': 50,
                'window_sec': 60,
                'window_rest_sec': 20,
                'max_consecutive_failures': 5,
                'pause_sec_on_failure': 60,
                'backoff_factor': 1.5,
                'cooldown_on_errno_-62_sec': 120
            }
        }
        
        with patch('core_service.BaiduPanAdapter'):
            service = CoreService(cookie='fake_cookie', config=config)
            
            # No workers running
            service.transfer_worker = None
            service.share_worker = None
            
            new_throttle_config = {
                'jitter_ms_min': 900,
                'jitter_ms_max': 1900,
                'ops_per_window': 25,
                'window_sec': 40,
                'window_rest_sec': 8,
                'max_consecutive_failures': 2,
                'pause_sec_on_failure': 50,
                'backoff_factor': 1.4,
                'cooldown_on_errno_-62_sec': 100
            }
            
            # Should not raise error
            service.update_throttle(new_throttle_config)
            
            # Throttler should be updated
            assert service.throttler.jitter_min == 900
            assert service.throttler.ops_per_window == 25
            
    def test_update_throttle_stopped_workers(self):
        """update_throttle should skip stopped workers."""
        config = {
            'throttle': {
                'jitter_ms_min': 500,
                'jitter_ms_max': 1500,
                'ops_per_window': 50,
                'window_sec': 60,
                'window_rest_sec': 20,
                'max_consecutive_failures': 5,
                'pause_sec_on_failure': 60,
                'backoff_factor': 1.5,
                'cooldown_on_errno_-62_sec': 120
            }
        }
        
        with patch('core_service.BaiduPanAdapter'):
            service = CoreService(cookie='fake_cookie', config=config)
            initial_throttler = service.throttler
            
            # Create stopped workers (not started)
            transfer_worker = FakeWorker(initial_throttler)
            share_worker = FakeWorker(initial_throttler)
            
            service.transfer_worker = transfer_worker
            service.share_worker = share_worker
            
            # Workers are not started (_started = False)
            
            new_throttle_config = {
                'jitter_ms_min': 650,
                'jitter_ms_max': 1650,
                'ops_per_window': 42,
                'window_sec': 62,
                'window_rest_sec': 16,
                'max_consecutive_failures': 8,
                'pause_sec_on_failure': 85,
                'backoff_factor': 1.65,
                'cooldown_on_errno_-62_sec': 165
            }
            
            # Should not update stopped workers
            service.update_throttle(new_throttle_config)
            
            # Service throttler should be updated
            assert service.throttler.jitter_min == 650
            
            # Workers still have old throttler (not updated since not alive)
            assert transfer_worker.throttler is initial_throttler
            assert share_worker.throttler is initial_throttler


class TestThrottlerBehavior:
    """Test Throttler runtime behavior."""
    
    def test_throttler_success_resets_failures(self):
        """on_success should reset consecutive failure count."""
        config = {'throttle': {'max_consecutive_failures': 5}}
        throttler = Throttler(config)
        
        throttler.consec_fail = 3
        throttler.on_success()
        
        assert throttler.consec_fail == 0
        
    def test_throttler_failure_increments_count(self):
        """on_failure should increment consecutive failure count."""
        config = {'throttle': {'max_consecutive_failures': 5, 'pause_sec_on_failure': 1}}
        throttler = Throttler(config)
        
        initial_count = throttler.consec_fail
        throttler.on_failure(errno=-1)
        
        assert throttler.consec_fail == initial_count + 1
        
    @patch('time.sleep')
    def test_throttler_errno_62_cooldown(self, mock_sleep):
        """on_failure with errno -62 should trigger cooldown."""
        config = {'throttle': {'cooldown_on_errno_-62_sec': 120}}
        throttler = Throttler(config)
        
        throttler.on_failure(errno=-62)
        
        mock_sleep.assert_called_with(120)
        
    @patch('time.sleep')
    def test_throttler_max_failures_pause(self, mock_sleep):
        """Reaching max consecutive failures should trigger pause."""
        config = {
            'throttle': {
                'max_consecutive_failures': 3,
                'pause_sec_on_failure': 60,
                'cooldown_on_errno_-62_sec': 0
            }
        }
        throttler = Throttler(config)
        
        # Trigger failures
        throttler.on_failure(errno=-1)
        throttler.on_failure(errno=-1)
        throttler.on_failure(errno=-1)
        
        # Should have paused
        mock_sleep.assert_called_with(60)
        # Failure count should be reset
        assert throttler.consec_fail == 0


class TestCoreServiceIntegration:
    """Integration tests for CoreService throttle updates."""
    
    def test_service_creates_throttler_on_init(self):
        """CoreService should create throttler during initialization."""
        config = {
            'throttle': {
                'jitter_ms_min': 500,
                'jitter_ms_max': 1500,
                'ops_per_window': 50,
                'window_sec': 60,
                'window_rest_sec': 20,
                'max_consecutive_failures': 5,
                'pause_sec_on_failure': 60,
                'backoff_factor': 1.5,
                'cooldown_on_errno_-62_sec': 120
            }
        }
        
        with patch('core_service.BaiduPanAdapter'):
            service = CoreService(cookie='fake_cookie', config=config)
            
            assert service.throttler is not None
            assert isinstance(service.throttler, Throttler)
            assert service.throttler.ops_per_window == 50
            
    def test_throttler_uses_updated_config(self):
        """Throttler should use new config values after update."""
        config = {
            'throttle': {
                'jitter_ms_min': 500,
                'jitter_ms_max': 1500,
                'ops_per_window': 50,
                'window_sec': 60,
                'window_rest_sec': 20,
                'max_consecutive_failures': 5,
                'pause_sec_on_failure': 60,
                'backoff_factor': 1.5,
                'cooldown_on_errno_-62_sec': 120
            },
            'other_setting': 'value'
        }
        
        with patch('core_service.BaiduPanAdapter'):
            service = CoreService(cookie='fake_cookie', config=config)
            
            new_throttle = {
                'jitter_ms_min': 1000,
                'jitter_ms_max': 2000,
                'ops_per_window': 30,
                'window_sec': 45,
                'window_rest_sec': 15,
                'max_consecutive_failures': 3,
                'pause_sec_on_failure': 90,
                'backoff_factor': 2.0,
                'cooldown_on_errno_-62_sec': 180
            }
            
            service.update_throttle(new_throttle)
            
            # Throttler should use new config values
            assert service.throttler.jitter_min == 1000
            assert service.throttler.jitter_max == 2000
            assert service.throttler.ops_per_window == 30
            assert service.throttler.window_sec == 45
