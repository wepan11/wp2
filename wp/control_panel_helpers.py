"""
Control Panel Helper Functions

Extracted helper functions for queue aggregation, health status,
and overview data generation. These functions are designed to be
testable independently of Flask routes.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime


def aggregate_queue_summary(services: Dict[str, Any]) -> Dict[str, int]:
    """
    Aggregate queue statistics across multiple service instances.
    
    Args:
        services: Dictionary mapping account names to CoreService instances
        
    Returns:
        Dictionary with aggregated queue counts for transfer and share operations
    """
    summary = {
        'total_transfer_pending': 0,
        'total_transfer_running': 0,
        'total_transfer_completed': 0,
        'total_transfer_failed': 0,
        'total_share_pending': 0,
        'total_share_running': 0,
        'total_share_completed': 0,
        'total_share_failed': 0
    }
    
    for account_name, service in services.items():
        if service is None:
            continue
            
        try:
            transfer_status = service.get_transfer_status()
            share_status = service.get_share_status()
            
            summary['total_transfer_pending'] += transfer_status.get('pending', 0)
            summary['total_transfer_running'] += transfer_status.get('running', 0)
            summary['total_transfer_completed'] += transfer_status.get('completed', 0)
            summary['total_transfer_failed'] += transfer_status.get('failed', 0)
            
            summary['total_share_pending'] += share_status.get('pending', 0)
            summary['total_share_running'] += share_status.get('running', 0)
            summary['total_share_completed'] += share_status.get('completed', 0)
            summary['total_share_failed'] += share_status.get('failed', 0)
        except Exception:
            # Skip services that fail to provide status
            continue
    
    return summary


def build_health_status(services: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build health status information for all services.
    
    Args:
        services: Dictionary mapping account names to CoreService instances
        
    Returns:
        Dictionary with health status including total accounts, active accounts, etc.
    """
    total_accounts = len(services)
    active_accounts = sum(1 for service in services.values() if service is not None)
    
    return {
        'status': 'healthy' if active_accounts > 0 else 'no_accounts',
        'total_accounts': total_accounts,
        'active_accounts': active_accounts,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }


def build_account_list(accounts: Dict[str, str], services: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Build list of account information with their status.
    
    Args:
        accounts: Dictionary mapping account names to cookie data
        services: Dictionary mapping account names to CoreService instances
        
    Returns:
        List of dictionaries with account information
    """
    account_list = []
    
    for account_name in accounts.keys():
        service = services.get(account_name)
        account_info = {
            'name': account_name,
            'available': service is not None,
            'has_adapter': hasattr(service, 'adapter') and service.adapter is not None if service else False
        }
        account_list.append(account_info)
    
    return account_list


def aggregate_account_queues(accounts: Dict[str, str], get_service_func) -> Dict[str, Any]:
    """
    Aggregate queue data for all accounts.
    
    Args:
        accounts: Dictionary mapping account names to cookie data
        get_service_func: Function to get or create service for an account
        
    Returns:
        Dictionary with timestamp and per-account queue data
    """
    result = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'accounts': {}
    }
    
    for account_name in accounts.keys():
        try:
            service = get_service_func(account_name)
            
            if not service:
                result['accounts'][account_name] = {
                    'available': False,
                    'error': 'Service unavailable or login failed'
                }
                continue
            
            # Get transfer status and queue
            transfer_status = service.get_transfer_status()
            transfer_queue = service.get_transfer_queue()
            
            # Get share status and queue
            share_status = service.get_share_status()
            share_queue = service.get_share_queue()
            
            # Build normalized account data
            result['accounts'][account_name] = {
                'available': True,
                'transfer': {
                    'status': {
                        'total': transfer_status.get('total', 0),
                        'pending': transfer_status.get('pending', 0),
                        'running': transfer_status.get('running', 0),
                        'completed': transfer_status.get('completed', 0),
                        'failed': transfer_status.get('failed', 0),
                        'skipped': transfer_status.get('skipped', 0),
                        'is_running': transfer_status.get('is_running', False),
                        'is_paused': transfer_status.get('is_paused', False)
                    },
                    'queue': transfer_queue
                },
                'share': {
                    'status': {
                        'total': share_status.get('total', 0),
                        'pending': share_status.get('pending', 0),
                        'running': share_status.get('running', 0),
                        'completed': share_status.get('completed', 0),
                        'failed': share_status.get('failed', 0),
                        'skipped': share_status.get('skipped', 0),
                        'is_running': share_status.get('is_running', False),
                        'is_paused': share_status.get('is_paused', False)
                    },
                    'queue': share_queue
                }
            }
        except Exception as e:
            result['accounts'][account_name] = {
                'available': False,
                'error': str(e)
            }
    
    return result


def build_overview_data(
    accounts: Dict[str, str],
    services: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Build complete overview data for control panel dashboard.
    
    Args:
        accounts: Dictionary mapping account names to cookie data
        services: Dictionary mapping account names to CoreService instances
        
    Returns:
        Dictionary with health status, account list, and queue summary
    """
    health_status = build_health_status(services)
    account_list = build_account_list(accounts, services)
    queues_summary = aggregate_queue_summary(services)
    
    return {
        'health': health_status,
        'accounts': account_list,
        'queues_summary': queues_summary
    }


def filter_queue_by_status(queue: List[Dict[str, Any]], status: str) -> List[Dict[str, Any]]:
    """
    Filter queue items by status.
    
    Args:
        queue: List of queue task dictionaries
        status: Status to filter by (e.g., 'pending', 'completed', 'failed')
        
    Returns:
        Filtered list of queue items
    """
    return [task for task in queue if task.get('status') == status]


def count_tasks_by_status(queue: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Count tasks in queue by status.
    
    Args:
        queue: List of queue task dictionaries
        
    Returns:
        Dictionary mapping status to count
    """
    counts = {
        'total': len(queue),
        'pending': 0,
        'running': 0,
        'completed': 0,
        'failed': 0,
        'skipped': 0
    }
    
    for task in queue:
        status = task.get('status', '')
        if status in counts:
            counts[status] += 1
    
    return counts
