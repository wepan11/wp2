"""
Unit tests for control panel helper functions.
Tests queue aggregation, health status, and overview data generation.
"""
import os
import sys
from unittest.mock import MagicMock, Mock
from datetime import datetime

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from control_panel_helpers import (
    aggregate_queue_summary,
    build_health_status,
    build_account_list,
    aggregate_account_queues,
    build_overview_data,
    filter_queue_by_status,
    count_tasks_by_status
)


class TestAggregateQueueSummary:
    """Test aggregate_queue_summary function."""
    
    def test_aggregate_empty_services(self):
        """Aggregating empty services should return zero counts."""
        services = {}
        result = aggregate_queue_summary(services)
        
        assert result['total_transfer_pending'] == 0
        assert result['total_transfer_running'] == 0
        assert result['total_transfer_completed'] == 0
        assert result['total_transfer_failed'] == 0
        assert result['total_share_pending'] == 0
        assert result['total_share_running'] == 0
        assert result['total_share_completed'] == 0
        assert result['total_share_failed'] == 0
        
    def test_aggregate_single_service(self):
        """Aggregating single service should return its counts."""
        mock_service = MagicMock()
        mock_service.get_transfer_status.return_value = {
            'pending': 5,
            'running': 2,
            'completed': 10,
            'failed': 1
        }
        mock_service.get_share_status.return_value = {
            'pending': 3,
            'running': 1,
            'completed': 8,
            'failed': 0
        }
        
        services = {'account1': mock_service}
        result = aggregate_queue_summary(services)
        
        assert result['total_transfer_pending'] == 5
        assert result['total_transfer_running'] == 2
        assert result['total_transfer_completed'] == 10
        assert result['total_transfer_failed'] == 1
        assert result['total_share_pending'] == 3
        assert result['total_share_running'] == 1
        assert result['total_share_completed'] == 8
        assert result['total_share_failed'] == 0
        
    def test_aggregate_multiple_services(self):
        """Aggregating multiple services should sum all counts."""
        mock_service1 = MagicMock()
        mock_service1.get_transfer_status.return_value = {
            'pending': 5,
            'running': 2,
            'completed': 10,
            'failed': 1
        }
        mock_service1.get_share_status.return_value = {
            'pending': 3,
            'running': 1,
            'completed': 8,
            'failed': 0
        }
        
        mock_service2 = MagicMock()
        mock_service2.get_transfer_status.return_value = {
            'pending': 3,
            'running': 1,
            'completed': 7,
            'failed': 2
        }
        mock_service2.get_share_status.return_value = {
            'pending': 2,
            'running': 0,
            'completed': 5,
            'failed': 1
        }
        
        services = {
            'account1': mock_service1,
            'account2': mock_service2
        }
        result = aggregate_queue_summary(services)
        
        assert result['total_transfer_pending'] == 8
        assert result['total_transfer_running'] == 3
        assert result['total_transfer_completed'] == 17
        assert result['total_transfer_failed'] == 3
        assert result['total_share_pending'] == 5
        assert result['total_share_running'] == 1
        assert result['total_share_completed'] == 13
        assert result['total_share_failed'] == 1
        
    def test_aggregate_with_none_service(self):
        """Aggregating with None services should skip them."""
        mock_service = MagicMock()
        mock_service.get_transfer_status.return_value = {
            'pending': 4,
            'running': 1,
            'completed': 6,
            'failed': 0
        }
        mock_service.get_share_status.return_value = {
            'pending': 2,
            'running': 0,
            'completed': 3,
            'failed': 0
        }
        
        services = {
            'account1': mock_service,
            'account2': None
        }
        result = aggregate_queue_summary(services)
        
        assert result['total_transfer_pending'] == 4
        assert result['total_share_completed'] == 3
        
    def test_aggregate_with_failing_service(self):
        """Aggregating with failing service should skip it."""
        mock_service1 = MagicMock()
        mock_service1.get_transfer_status.return_value = {
            'pending': 3,
            'running': 0,
            'completed': 5,
            'failed': 1
        }
        mock_service1.get_share_status.return_value = {
            'pending': 1,
            'running': 0,
            'completed': 2,
            'failed': 0
        }
        
        mock_service2 = MagicMock()
        mock_service2.get_transfer_status.side_effect = Exception("Service error")
        
        services = {
            'account1': mock_service1,
            'account2': mock_service2
        }
        result = aggregate_queue_summary(services)
        
        # Should only include account1
        assert result['total_transfer_pending'] == 3
        assert result['total_share_pending'] == 1
        
    def test_aggregate_with_missing_status_keys(self):
        """Aggregating with missing status keys should default to 0."""
        mock_service = MagicMock()
        mock_service.get_transfer_status.return_value = {
            'pending': 2
            # Missing other keys
        }
        mock_service.get_share_status.return_value = {
            'completed': 5
            # Missing other keys
        }
        
        services = {'account1': mock_service}
        result = aggregate_queue_summary(services)
        
        assert result['total_transfer_pending'] == 2
        assert result['total_transfer_running'] == 0
        assert result['total_share_completed'] == 5
        assert result['total_share_pending'] == 0


class TestBuildHealthStatus:
    """Test build_health_status function."""
    
    def test_health_status_no_services(self):
        """Health status with no services should indicate no accounts."""
        services = {}
        result = build_health_status(services)
        
        assert result['status'] == 'no_accounts'
        assert result['total_accounts'] == 0
        assert result['active_accounts'] == 0
        assert 'timestamp' in result
        
    def test_health_status_all_active(self):
        """Health status with all active services should be healthy."""
        services = {
            'account1': MagicMock(),
            'account2': MagicMock()
        }
        result = build_health_status(services)
        
        assert result['status'] == 'healthy'
        assert result['total_accounts'] == 2
        assert result['active_accounts'] == 2
        
    def test_health_status_some_inactive(self):
        """Health status with some inactive services should still be healthy."""
        services = {
            'account1': MagicMock(),
            'account2': None,
            'account3': MagicMock()
        }
        result = build_health_status(services)
        
        assert result['status'] == 'healthy'
        assert result['total_accounts'] == 3
        assert result['active_accounts'] == 2
        
    def test_health_status_all_inactive(self):
        """Health status with all inactive services should indicate no accounts."""
        services = {
            'account1': None,
            'account2': None
        }
        result = build_health_status(services)
        
        assert result['status'] == 'no_accounts'
        assert result['total_accounts'] == 2
        assert result['active_accounts'] == 0
        
    def test_health_status_timestamp_format(self):
        """Health status timestamp should be in correct format."""
        services = {'account1': MagicMock()}
        result = build_health_status(services)
        
        # Verify timestamp format
        timestamp = result['timestamp']
        datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')


class TestBuildAccountList:
    """Test build_account_list function."""
    
    def test_account_list_empty(self):
        """Account list with no accounts should be empty."""
        accounts = {}
        services = {}
        result = build_account_list(accounts, services)
        
        assert result == []
        
    def test_account_list_available_accounts(self):
        """Account list should show available accounts."""
        mock_service = MagicMock()
        mock_service.adapter = MagicMock()
        
        accounts = {'account1': 'cookie1'}
        services = {'account1': mock_service}
        result = build_account_list(accounts, services)
        
        assert len(result) == 1
        assert result[0]['name'] == 'account1'
        assert result[0]['available'] is True
        assert result[0]['has_adapter'] is True
        
    def test_account_list_unavailable_accounts(self):
        """Account list should show unavailable accounts."""
        accounts = {'account1': 'cookie1'}
        services = {'account1': None}
        result = build_account_list(accounts, services)
        
        assert len(result) == 1
        assert result[0]['name'] == 'account1'
        assert result[0]['available'] is False
        assert result[0]['has_adapter'] is False
        
    def test_account_list_mixed_availability(self):
        """Account list should handle mixed availability."""
        mock_service1 = MagicMock()
        mock_service1.adapter = MagicMock()
        
        mock_service2 = MagicMock()
        mock_service2.adapter = None
        
        accounts = {
            'account1': 'cookie1',
            'account2': 'cookie2',
            'account3': 'cookie3'
        }
        services = {
            'account1': mock_service1,
            'account2': mock_service2,
            'account3': None
        }
        result = build_account_list(accounts, services)
        
        assert len(result) == 3
        assert result[0]['name'] == 'account1'
        assert result[0]['available'] is True
        assert result[0]['has_adapter'] is True
        
        assert result[1]['name'] == 'account2'
        assert result[1]['available'] is True
        assert result[1]['has_adapter'] is False
        
        assert result[2]['name'] == 'account3'
        assert result[2]['available'] is False


class TestAggregateAccountQueues:
    """Test aggregate_account_queues function."""
    
    def test_aggregate_queues_single_account(self):
        """Aggregating queues for single account."""
        mock_service = MagicMock()
        mock_service.get_transfer_status.return_value = {
            'total': 5,
            'pending': 2,
            'running': 1,
            'completed': 2,
            'failed': 0,
            'skipped': 0,
            'is_running': True,
            'is_paused': False
        }
        mock_service.get_transfer_queue.return_value = [
            {'status': 'pending', 'share_link': 'link1'},
            {'status': 'running', 'share_link': 'link2'}
        ]
        mock_service.get_share_status.return_value = {
            'total': 3,
            'pending': 1,
            'running': 0,
            'completed': 2,
            'failed': 0,
            'skipped': 0,
            'is_running': False,
            'is_paused': False
        }
        mock_service.get_share_queue.return_value = [
            {'status': 'completed', 'share_link': 'share1'}
        ]
        
        def get_service_func(account_name):
            return mock_service
        
        accounts = {'account1': 'cookie1'}
        result = aggregate_account_queues(accounts, get_service_func)
        
        assert 'timestamp' in result
        assert 'accounts' in result
        assert 'account1' in result['accounts']
        
        account_data = result['accounts']['account1']
        assert account_data['available'] is True
        assert account_data['transfer']['status']['pending'] == 2
        assert account_data['transfer']['status']['is_running'] is True
        assert len(account_data['transfer']['queue']) == 2
        assert account_data['share']['status']['completed'] == 2
        
    def test_aggregate_queues_unavailable_service(self):
        """Aggregating queues with unavailable service."""
        def get_service_func(account_name):
            return None
        
        accounts = {'account1': 'cookie1'}
        result = aggregate_account_queues(accounts, get_service_func)
        
        assert result['accounts']['account1']['available'] is False
        assert 'error' in result['accounts']['account1']
        
    def test_aggregate_queues_service_error(self):
        """Aggregating queues with service throwing error."""
        mock_service = MagicMock()
        mock_service.get_transfer_status.side_effect = Exception("Connection error")
        
        def get_service_func(account_name):
            return mock_service
        
        accounts = {'account1': 'cookie1'}
        result = aggregate_account_queues(accounts, get_service_func)
        
        assert result['accounts']['account1']['available'] is False
        assert 'error' in result['accounts']['account1']
        assert 'Connection error' in result['accounts']['account1']['error']
        
    def test_aggregate_queues_multiple_accounts(self):
        """Aggregating queues for multiple accounts."""
        mock_service1 = MagicMock()
        mock_service1.get_transfer_status.return_value = {
            'total': 2, 'pending': 1, 'running': 0, 'completed': 1,
            'failed': 0, 'skipped': 0, 'is_running': False, 'is_paused': False
        }
        mock_service1.get_transfer_queue.return_value = []
        mock_service1.get_share_status.return_value = {
            'total': 1, 'pending': 0, 'running': 0, 'completed': 1,
            'failed': 0, 'skipped': 0, 'is_running': False, 'is_paused': False
        }
        mock_service1.get_share_queue.return_value = []
        
        mock_service2 = MagicMock()
        mock_service2.get_transfer_status.return_value = {
            'total': 3, 'pending': 2, 'running': 1, 'completed': 0,
            'failed': 0, 'skipped': 0, 'is_running': True, 'is_paused': False
        }
        mock_service2.get_transfer_queue.return_value = []
        mock_service2.get_share_status.return_value = {
            'total': 2, 'pending': 1, 'running': 0, 'completed': 1,
            'failed': 0, 'skipped': 0, 'is_running': False, 'is_paused': False
        }
        mock_service2.get_share_queue.return_value = []
        
        services_map = {
            'account1': mock_service1,
            'account2': mock_service2
        }
        
        def get_service_func(account_name):
            return services_map.get(account_name)
        
        accounts = {'account1': 'cookie1', 'account2': 'cookie2'}
        result = aggregate_account_queues(accounts, get_service_func)
        
        assert len(result['accounts']) == 2
        assert result['accounts']['account1']['available'] is True
        assert result['accounts']['account2']['available'] is True
        assert result['accounts']['account1']['transfer']['status']['pending'] == 1
        assert result['accounts']['account2']['transfer']['status']['running'] == 1


class TestBuildOverviewData:
    """Test build_overview_data function."""
    
    def test_overview_data_complete(self):
        """Overview data should include all components."""
        mock_service = MagicMock()
        mock_service.adapter = MagicMock()
        mock_service.get_transfer_status.return_value = {
            'pending': 3, 'running': 1, 'completed': 5, 'failed': 0
        }
        mock_service.get_share_status.return_value = {
            'pending': 2, 'running': 0, 'completed': 4, 'failed': 1
        }
        
        accounts = {'account1': 'cookie1'}
        services = {'account1': mock_service}
        
        result = build_overview_data(accounts, services)
        
        assert 'health' in result
        assert 'accounts' in result
        assert 'queues_summary' in result
        
        assert result['health']['status'] == 'healthy'
        assert len(result['accounts']) == 1
        assert result['queues_summary']['total_transfer_pending'] == 3
        assert result['queues_summary']['total_share_completed'] == 4
        
    def test_overview_data_no_accounts(self):
        """Overview data with no accounts."""
        accounts = {}
        services = {}
        
        result = build_overview_data(accounts, services)
        
        assert result['health']['status'] == 'no_accounts'
        assert result['accounts'] == []
        assert result['queues_summary']['total_transfer_pending'] == 0


class TestFilterQueueByStatus:
    """Test filter_queue_by_status function."""
    
    def test_filter_empty_queue(self):
        """Filtering empty queue should return empty list."""
        queue = []
        result = filter_queue_by_status(queue, 'pending')
        
        assert result == []
        
    def test_filter_queue_by_pending(self):
        """Filtering queue by pending status."""
        queue = [
            {'status': 'pending', 'id': 1},
            {'status': 'running', 'id': 2},
            {'status': 'pending', 'id': 3},
            {'status': 'completed', 'id': 4}
        ]
        result = filter_queue_by_status(queue, 'pending')
        
        assert len(result) == 2
        assert all(item['status'] == 'pending' for item in result)
        
    def test_filter_queue_by_completed(self):
        """Filtering queue by completed status."""
        queue = [
            {'status': 'pending', 'id': 1},
            {'status': 'completed', 'id': 2},
            {'status': 'completed', 'id': 3}
        ]
        result = filter_queue_by_status(queue, 'completed')
        
        assert len(result) == 2
        
    def test_filter_queue_no_matches(self):
        """Filtering queue with no matches."""
        queue = [
            {'status': 'pending', 'id': 1},
            {'status': 'running', 'id': 2}
        ]
        result = filter_queue_by_status(queue, 'failed')
        
        assert result == []


class TestCountTasksByStatus:
    """Test count_tasks_by_status function."""
    
    def test_count_empty_queue(self):
        """Counting empty queue."""
        queue = []
        result = count_tasks_by_status(queue)
        
        assert result['total'] == 0
        assert result['pending'] == 0
        assert result['running'] == 0
        assert result['completed'] == 0
        assert result['failed'] == 0
        assert result['skipped'] == 0
        
    def test_count_tasks_various_statuses(self):
        """Counting tasks with various statuses."""
        queue = [
            {'status': 'pending'},
            {'status': 'pending'},
            {'status': 'running'},
            {'status': 'completed'},
            {'status': 'completed'},
            {'status': 'completed'},
            {'status': 'failed'}
        ]
        result = count_tasks_by_status(queue)
        
        assert result['total'] == 7
        assert result['pending'] == 2
        assert result['running'] == 1
        assert result['completed'] == 3
        assert result['failed'] == 1
        assert result['skipped'] == 0
        
    def test_count_tasks_with_skipped(self):
        """Counting tasks including skipped status."""
        queue = [
            {'status': 'completed'},
            {'status': 'skipped'},
            {'status': 'skipped'}
        ]
        result = count_tasks_by_status(queue)
        
        assert result['total'] == 3
        assert result['completed'] == 1
        assert result['skipped'] == 2
        
    def test_count_tasks_missing_status(self):
        """Counting tasks with missing status field."""
        queue = [
            {'status': 'pending'},
            {'id': 1},  # Missing status
            {'status': 'completed'}
        ]
        result = count_tasks_by_status(queue)
        
        assert result['total'] == 3
        assert result['pending'] == 1
        assert result['completed'] == 1
