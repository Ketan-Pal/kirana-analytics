import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture(scope="session")
def client():
    """Provides a TestClient fixture across the test session."""
    with TestClient(app) as test_client:
        yield test_client
