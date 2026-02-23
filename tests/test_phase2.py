"""Tests for Phase 2 features: POST, path params, pagination, seeding, errors."""

from pydantic import BaseModel

from semblance import (
    PageParams,
    PaginatedResponse,
    SemblanceAPI,
)
from semblance import (
    test_client as client_for,
)
from tests.example_models import User, UserQuery


class CreateUserRequest(BaseModel):
    """POST body for creating a user."""

    name: str
    start_date: str = "2020-01-01"
    end_date: str = "2025-12-31"


class UserGetInput(BaseModel):
    """Input for GET /users/{id} - id from path, name from query.
    Path param id must have default for query validation to pass.
    """

    id: str = ""
    name: str = "alice"


class UserListQuery(PageParams, BaseModel):
    """Query with pagination params."""

    name: str = "alice"


def test_post_with_body():
    """POST endpoint with body model generates response from body."""
    api = SemblanceAPI()
    api.post("/users", input=CreateUserRequest, output=User)(lambda: None)
    app = api.as_fastapi()
    client = client_for(app)
    r = client.post("/users", json={"name": "postuser"})
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "postuser"


def test_get_with_path_param():
    """GET /users/{id} with path param in input model."""
    api = SemblanceAPI()
    api.get("/users/{id}", input=UserGetInput, output=User)(lambda: None)
    app = api.as_fastapi()
    client = client_for(app)
    r = client.get("/users/user-123?name=pathuser")
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "pathuser"
    # Path param id is available for FromInput if needed


def test_list_count_from_input():
    """list_count='limit' uses input field for list length."""

    class UserQueryWithLimit(BaseModel):
        name: str = "alice"
        limit: int = 3

    # Need input model with limit - UserQuery doesn't have limit
    api2 = SemblanceAPI()
    api2.get(
        "/users2", input=UserQueryWithLimit, output=list[User], list_count="limit"
    )(lambda: None)
    app2 = api2.as_fastapi()
    client2 = client_for(app2)
    r = client2.get("/users2?name=x&limit=4")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 4


def test_paginated_response():
    """PaginatedResponse[User] returns items, total, limit, offset."""
    api = SemblanceAPI()
    api.get("/users", input=UserListQuery, output=PaginatedResponse[User])(lambda: None)
    app = api.as_fastapi()
    client = client_for(app)
    r = client.get("/users?name=paged&limit=3&offset=1")
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data
    assert data["limit"] == 3
    assert data["offset"] == 1
    assert len(data["items"]) <= 3


def test_deterministic_seed():
    """seed=42 produces same responses across requests."""
    api = SemblanceAPI(seed=42)
    api.get("/users", input=UserQuery, output=list[User], list_count=2)(lambda: None)
    app = api.as_fastapi()
    client = client_for(app)
    r1 = client.get("/users?name=seed")
    r2 = client.get("/users?name=seed")
    assert r1.status_code == 200 and r2.status_code == 200
    d1 = r1.json()
    d2 = r2.json()
    assert d1[0]["created_at"] == d2[0]["created_at"]
    assert d1[1]["created_at"] == d2[1]["created_at"]


def test_seed_from_input():
    """seed_from='seed' uses query param for determinism."""

    class UserQueryWithSeed(BaseModel):
        name: str = "alice"
        seed: int | None = None

    api = SemblanceAPI()
    api.get(
        "/users",
        input=UserQueryWithSeed,
        output=list[User],
        list_count=2,
        seed_from="seed",
    )(lambda: None)
    app = api.as_fastapi()
    client = client_for(app)
    r1 = client.get("/users?name=x&seed=99")
    r2 = client.get("/users?name=x&seed=99")
    assert r1.status_code == 200 and r2.status_code == 200
    d1 = r1.json()
    d2 = r2.json()
    assert d1[0]["created_at"] == d2[0]["created_at"]


def test_error_rate_zero_returns_success():
    """error_rate=0 never returns errors."""
    api = SemblanceAPI()
    api.get("/users", input=UserQuery, output=list[User], error_rate=0)(lambda: None)
    app = api.as_fastapi()
    client = client_for(app)
    for _ in range(5):
        r = client.get("/users?name=x")
        assert r.status_code == 200


def test_error_rate_one_returns_errors():
    """error_rate=1.0 always returns an error."""
    api = SemblanceAPI()
    api.get(
        "/users",
        input=UserQuery,
        output=list[User],
        error_rate=1.0,
        error_codes=[418],
    )(lambda: None)
    app = api.as_fastapi()
    client = client_for(app)
    r = client.get("/users?name=x")
    assert r.status_code == 418


def test_post_with_path_param():
    """POST /users/{id} with path param merges path into body for build_response."""

    class CreateUserWithId(BaseModel):
        id: str = ""
        name: str

    api = SemblanceAPI()
    api.post("/users/{id}", input=CreateUserWithId, output=User)(lambda: None)
    app = api.as_fastapi()
    client = client_for(app)
    r = client.post("/users/user-456", json={"name": "pathpost"})
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "pathpost"


def test_post_with_seed_from_input():
    """seed_from='seed' uses body field for determinism on POST."""

    class CreateWithSeed(BaseModel):
        name: str
        seed: int | None = None
        start_date: str = "2020-01-01"
        end_date: str = "2020-12-31"

    api = SemblanceAPI()
    api.post(
        "/users",
        input=CreateWithSeed,
        output=User,
        seed_from="seed",
    )(lambda: None)
    app = api.as_fastapi()
    client = client_for(app)
    body = {"name": "seedpost", "seed": 77}
    r1 = client.post("/users", json=body)
    r2 = client.post("/users", json=body)
    assert r1.status_code == 200 and r2.status_code == 200
    d1 = r1.json()
    d2 = r2.json()
    assert d1["created_at"] == d2["created_at"]


def test_list_count_fallback_when_field_invalid():
    """list_count='limit' falls back to 5 when limit cannot be coerced to int."""

    class QueryWithInvalidLimit(BaseModel):
        name: str = "x"
        limit: str = "not-a-number"

    api = SemblanceAPI()
    api.get(
        "/users",
        input=QueryWithInvalidLimit,
        output=list[User],
        list_count="limit",
    )(lambda: None)
    app = api.as_fastapi()
    client = client_for(app)
    r = client.get("/users?name=x&limit=abc")
    assert r.status_code == 200
    # Falls back to 5 when int("abc") fails
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 5
