"""Pytest fixtures for Semblance tests."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from semblance import SemblanceAPI
from semblance import test_client as client_for


@pytest.fixture
def app_fixture() -> FastAPI:
    """Build a minimal Semblance app for tests that use semblance_client fixture."""
    from tests.example_models import User, UserQuery

    api = SemblanceAPI()
    api.get("/users", input=UserQuery, output=list[User], list_count=3)(lambda: None)
    api.get("/user", input=UserQuery, output=User)(lambda: None)
    return api.as_fastapi()


@pytest.fixture
def semblance_client(app_fixture: FastAPI) -> TestClient:
    """TestClient for the example Semblance app."""
    return client_for(app_fixture)
