"""Tests for mount_into and middleware."""

from fastapi import FastAPI

from semblance import SemblanceAPI
from semblance.testing import test_client as make_client
from tests.example_models import User, UserQuery


def test_mount_into_prefix():
    api = SemblanceAPI()
    api.get("/users", input=UserQuery, output=list[User], list_count=1)(lambda: None)
    parent = FastAPI()
    api.mount_into(parent, "/api")
    client = make_client(parent)
    r = client.get("/api/users?name=alice")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["name"] == "alice"


def test_mount_into_root():
    api = SemblanceAPI()
    api.get("/items", input=UserQuery, output=list[User], list_count=1)(lambda: None)
    parent = FastAPI()
    api.mount_into(parent, "/")
    client = make_client(parent)
    assert client.get("/items?name=x").status_code == 200


def test_add_middleware_adds_header():
    from starlette.middleware.base import BaseHTTPMiddleware

    class AddHeaderMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            response = await call_next(request)
            response.headers["X-Semblance-Test"] = "ok"
            return response

    api = SemblanceAPI()
    api.get("/users", input=UserQuery, output=list[User], list_count=1)(lambda: None)
    api.add_middleware(AddHeaderMiddleware)
    client = make_client(api.as_fastapi())
    r = client.get("/users?name=x")
    assert r.status_code == 200
    assert r.headers.get("X-Semblance-Test") == "ok"
