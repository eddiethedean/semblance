"""
Testing utilities for Semblance APIs.

Provides test_client for FastAPI apps built with SemblanceAPI.as_fastapi().
"""

from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_client(app: FastAPI, **kwargs: Any) -> TestClient:
    """
    Return an httpx TestClient for the given FastAPI app.

    Use with SemblanceAPI.as_fastapi() for integration tests:

        api = SemblanceAPI()
        api.get("/users", input=UserQuery, output=list[User])(lambda: None)
        app = api.as_fastapi()
        client = test_client(app)
        r = client.get("/users?name=alice")
        assert r.status_code == 200
        data = r.json()
    """
    return TestClient(app, **kwargs)
