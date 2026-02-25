import pytest
import os
import shutil
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture(scope="session", autouse=True)
def setup_test_dirs():
    """Ensure test directories exist and are clean."""
    os.makedirs("test_downloads", exist_ok=True)
    os.makedirs("test_output", exist_ok=True)
    yield
    # Cleanup after all tests
    if os.path.exists("test_downloads"):
        shutil.rmtree("test_downloads")
    if os.path.exists("test_output"):
        shutil.rmtree("test_output")
