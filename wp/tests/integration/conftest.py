"""
Pytest configuration for integration tests.
Sets up test client with fakes to avoid real Baidu API calls.
"""
import pytest
from typing import Dict, Any, List, Optional
from unittest.mock import MagicMock


class FakeCoreService:
    """
    Lightweight fake CoreService that returns deterministic data.
    
    This stub responds to all CoreService methods that backend APIs call
    without making real Baidu network requests.
    
    Extend this class for new control panel endpoints by adding
    corresponding methods with deterministic payloads.
    """
    
    def __init__(self, cookie: str = None, config: Dict[str, Any] = None):
        self.cookie = cookie
        self.config = config or {}
        self.adapter = MagicMock()  # Mock adapter to satisfy checks
        self.transfer_queue = []
        self.share_queue = []
        self._should_fail = False
        
    def set_should_fail(self, should_fail: bool = True):
        """Control whether operations should return errors."""
        self._should_fail = should_fail
        
    def list_dir(self, path: str) -> List[Dict[str, Any]]:
        """Return fake file list or error code."""
        if self._should_fail:
            return -1  # Error code
        return [
            {
                'fs_id': 123456,
                'path': f'{path}/file1.txt',
                'server_filename': 'file1.txt',
                'size': 1024,
                'isdir': 0
            },
            {
                'fs_id': 123457,
                'path': f'{path}/folder1',
                'server_filename': 'folder1',
                'size': 0,
                'isdir': 1
            }
        ]
    
    def search_files(self, keyword: str, path: str = '/') -> List[Dict[str, Any]]:
        """Return fake search results."""
        if self._should_fail:
            return []
        return [
            {
                'fs_id': 789012,
                'path': f'/search/result_{keyword}.txt',
                'server_filename': f'result_{keyword}.txt',
                'size': 2048
            }
        ]
    
    def get_transfer_status(self) -> Dict[str, Any]:
        """Return fake transfer status."""
        return {
            'total': 10,
            'pending': 3,
            'running': 1,
            'completed': 5,
            'failed': 1,
            'skipped': 0,
            'is_running': False,
            'is_paused': False,
            'tasks': self.transfer_queue
        }
    
    def get_transfer_queue(self) -> List[Dict[str, Any]]:
        """Return fake transfer queue."""
        return self.transfer_queue or [
            {
                'share_link': 'https://pan.baidu.com/s/test1',
                'share_password': 'abc1',
                'target_path': '/batch_save',
                'status': 'pending'
            },
            {
                'share_link': 'https://pan.baidu.com/s/test2',
                'share_password': 'abc2',
                'target_path': '/batch_save',
                'status': 'completed'
            }
        ]
    
    def get_share_status(self) -> Dict[str, Any]:
        """Return fake share status."""
        return {
            'total': 8,
            'pending': 2,
            'running': 0,
            'completed': 6,
            'failed': 0,
            'skipped': 0,
            'is_running': False,
            'is_paused': False,
            'tasks': self.share_queue
        }
    
    def get_share_queue(self) -> List[Dict[str, Any]]:
        """Return fake share queue."""
        return self.share_queue or [
            {
                'file_info': {
                    'fs_id': 111,
                    'name': 'doc1.pdf',
                    'path': '/docs/doc1.pdf'
                },
                'status': 'completed',
                'share_link': 'https://pan.baidu.com/s/share1',
                'share_password': 'xyz1'
            },
            {
                'file_info': {
                    'fs_id': 222,
                    'name': 'doc2.pdf',
                    'path': '/docs/doc2.pdf'
                },
                'status': 'pending',
                'share_link': '',
                'share_password': ''
            }
        ]


@pytest.fixture
def fake_accounts():
    """Fake account credentials."""
    return {
        'test_account': 'fake_cookie_data',
        'test_account2': 'fake_cookie_data_2'
    }


@pytest.fixture
def fake_services(fake_accounts):
    """Fake service instances mapped to accounts."""
    services = {}
    for account, cookie in fake_accounts.items():
        service = FakeCoreService(cookie=cookie)
        services[account] = service
    return services


@pytest.fixture
def app_with_fakes(monkeypatch, fake_accounts, fake_services):
    """
    Flask test app with monkeypatched load_accounts_from_env and get_or_create_service.
    
    This fixture:
    - Uses testing config
    - Replaces account loading with fake data
    - Replaces service creation with fake services
    - Ensures no real Baidu API calls
    """
    # Import server module - use sys.path manipulation to import from parent
    import sys
    import os
    # Add parent directory to path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    
    import server as server_module
    from config import get_config
    
    # Get testing config
    test_config = get_config('testing')
    
    # Monkeypatch load_accounts_from_env to return fake accounts
    def fake_load_accounts():
        server_module.accounts.clear()
        server_module.accounts.update(fake_accounts)
        return True
    
    monkeypatch.setattr(server_module, 'load_accounts_from_env', fake_load_accounts)
    
    # Monkeypatch get_or_create_service to return fake services
    def fake_get_or_create_service(account: Optional[str] = None) -> Optional[FakeCoreService]:
        if not account:
            account = test_config.DEFAULT_ACCOUNT
        # Fallback to first available account if default not found
        if account not in fake_services:
            if fake_services:
                account = list(fake_services.keys())[0]
            else:
                return None
        return fake_services.get(account)
    
    monkeypatch.setattr(server_module, 'get_or_create_service', fake_get_or_create_service)
    
    # Initialize accounts
    fake_load_accounts()
    
    # Configure app for testing
    server_module.app.config['TESTING'] = True
    
    return server_module.app


@pytest.fixture
def client(app_with_fakes):
    """Flask test client."""
    with app_with_fakes.test_client() as client:
        yield client


@pytest.fixture
def api_key():
    """Valid API key for testing."""
    import sys
    import os
    # Add parent directory to path if not already there
    parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from config import get_config
    config = get_config('testing')
    return config.API_SECRET_KEY


@pytest.fixture
def auth_headers(api_key):
    """Headers with valid API key."""
    return {'X-API-Key': api_key}
