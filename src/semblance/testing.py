"""
Pytest utilities for Semblance APIs.

Provides a test client fixture that works with SemblanceAPI.as_fastapi().
"""

from typing import Any, Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def semblance_client(app_fixture: "SemblanceAPIFixture") -> Generator[TestClient, None, None]:
    """
    Yield a TestClient for the given Semblance FastAPI app.

    Requires a fixture named `app_fixture` that returns the FastAPI app
    (e.g. from api.as_fastapi()). Define in your conftest.py:

        @pytest.fixture
        def app_fixture():
            api = SemblanceAPI()
            # ... register endpoints ...
            return api.as_fastapi()

    Then use:
        def test_users(semblance_client):
            r = semblance_client.get("/users?name=alice")
            assert r.status_code == 200
    """
    app = app_fixture
    with TestClient(app) as client:
        yield client


def test_client(app: FastAPI, **kwargs: Any) -> TestClient:
    """
    Return a TestClient for the given FastAPI app.

    Use with SemblanceAPI.as_fastapi():

        api = SemblanceAPI()
        # ... register endpoints ...
        app = api.as_fastapi()
        client = semblance.test_client(app)
        r = client.get("/users?name=alice")
        assert r.status_code == 200
    """
    return TestClient(app, **kwargs)


# Type alias for fixtures that provide a FastAPI app
SemblanceAPIFixture = FastAPI
