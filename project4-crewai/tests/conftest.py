"""
Pytest configuration and fixtures
"""
import pytest
import os
from src.core.config import set_config, Config


@pytest.fixture(autouse=True)
def set_test_api_key(monkeypatch):
    """Automatically set test API key for all tests"""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-for-testing")
    # Reset config to ensure clean state
    set_config(Config(api_key="test-key-for-testing"))
