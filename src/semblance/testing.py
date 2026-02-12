"""
Pytest utilities for Semblance APIs.

Provides test client helpers for SemblanceAPI.as_fastapi().
"""

from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient


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
