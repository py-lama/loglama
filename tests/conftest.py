"""
Pytest fixtures for tests
"""
import pytest
import os
import sys

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def mock_env_vars(monkeypatch):
    """Fixture to set up environment variables for tests"""
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("API_PORT", "8080")
    
    return {
        "LOG_LEVEL": "DEBUG",
        "API_PORT": "8080"
    }
