"""Tests for SemblanceAPI, GET endpoints, and FastAPI app export."""

import pytest

from semblance import SemblanceAPI
from semblance import test_client as client_for
from tests.example_models import User, UserQuery


@pytest.fixture
def api():
    api = SemblanceAPI()
    api.get("/users", input=UserQuery, output=list[User], list_count=2)(lambda: None)
    api.get("/user", input=UserQuery, output=User)(lambda: None)
    return api


def test_as_fastapi_returns_app(api):
    app = api.as_fastapi()
    assert app is not None
    routes = [r.path for r in app.routes if hasattr(r, "path")]
    assert "/users" in routes
    assert "/user" in routes


def test_get_users_returns_list(api):
    client = client_for(api.as_fastapi())
    r = client.get("/users?name=testuser")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 2
    for item in data:
        assert item["name"] == "testuser"
        assert "created_at" in item


def test_get_user_single_returns_one(api):
    client = client_for(api.as_fastapi())
    r = client.get("/user?name=solo")
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "solo"
    assert "created_at" in data


def test_from_input_binding(api):
    client = client_for(api.as_fastapi())
    r = client.get("/user?name=bound")
    assert r.status_code == 200
    assert r.json()["name"] == "bound"


def test_date_range_in_range(api):
    client = client_for(api.as_fastapi())
    r = client.get("/user?name=x&start_date=2024-01-01&end_date=2024-12-31")
    assert r.status_code == 200
    created = r.json()["created_at"]
    assert "2024" in created
