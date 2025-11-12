"""
Shared pytest configuration and fixtures for all test suites.
This conftest.py provides fixtures that can be used by both unit and integration tests.
"""
import pytest
import tempfile
import os


@pytest.fixture
def tmp_path():
    """
    Provide a temporary directory path that is cleaned up after the test.
    This is a simplified version of pytest's built-in tmp_path fixture
    for compatibility.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def clean_env(monkeypatch):
    """
    Provide a clean environment without interfering with system environment.
    Useful for testing configuration loading.
    """
    # Store original env vars
    original_env = os.environ.copy()
    
    yield monkeypatch
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)
