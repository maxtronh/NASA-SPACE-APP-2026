import os
import sys

import pytest
from fastapi.testclient import TestClient

# Ensure workspace is on sys.path
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from backend.app.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Synchronous test client for backend API testing."""
    return TestClient(app)
