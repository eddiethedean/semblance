"""Tests for Phase 3 features: latency, conditional deps, nested, cross-field, filtering, stateful."""

import time
from typing import Annotated

from pydantic import BaseModel

from semblance import (
    ComputedFrom,
    SemblanceAPI,
    FromInput,
    WhenInput,
    test_client as client_for,
)

from tests.example_models import User, UserQuery


def test_latency_ms_adds_delay():
    """latency_ms adds delay before response."""
    api = SemblanceAPI()
    api.get("/users", input=UserQuery, output=list[User], list_count=1, latency_ms=50)(
        lambda: None
    )
    app = api.as_fastapi()
    client = client_for(app)
    start = time.perf_counter()
    r = client.get("/users?name=latency")
    elapsed = time.perf_counter() - start
    assert r.status_code == 200
    assert elapsed >= 0.045  # Allow some tolerance (50ms)


def test_latency_zero_no_delay():
    """latency_ms=0 and jitter_ms=0 return immediately."""
    api = SemblanceAPI()
    api.get("/users", input=UserQuery, output=list[User], list_count=1)(lambda: None)
    app = api.as_fastapi()
    client = client_for(app)
    start = time.perf_counter()
    r = client.get("/users?name=fast")
    elapsed = time.perf_counter() - start
    assert r.status_code == 200
    assert elapsed < 0.1


def test_when_input_condition_met_applies_link():
    """WhenInput applies inner link when condition is met."""

    class UserWithStatus(BaseModel):
        name: Annotated[str, FromInput("name")]
        status: Annotated[str, WhenInput("include_status", True, FromInput("status"))]

    class QueryWithStatus(BaseModel):
        name: str = "alice"
        status: str = "active"
        include_status: bool = False

    api = SemblanceAPI()
    api.get("/user", input=QueryWithStatus, output=UserWithStatus)(lambda: None)
    app = api.as_fastapi()
    client = client_for(app)

    r = client.get("/user?name=x&status=admin&include_status=true")
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "x"
    assert data["status"] == "admin"


def test_when_input_condition_not_met_uses_generated():
    """WhenInput skips override when condition is not met; Polyfactory generates."""
    from semblance.resolver import resolve_overrides

    class UserWithStatus(BaseModel):
        status: Annotated[str, WhenInput("include_status", True, FromInput("status"))]

    class QueryWithStatus(BaseModel):
        status: str = "active"
        include_status: bool = False

    overrides = resolve_overrides(UserWithStatus, QueryWithStatus, QueryWithStatus())
    assert "status" not in overrides


def test_nested_model_linking():
    """Nested model with FromInput resolves links from input."""

    class Address(BaseModel):
        city: Annotated[str, FromInput("city")]

    class UserWithAddress(BaseModel):
        name: Annotated[str, FromInput("name")]
        address: Address

    class QueryWithCity(BaseModel):
        name: str = "alice"
        city: str = "NYC"

    api = SemblanceAPI()
    api.get("/user", input=QueryWithCity, output=UserWithAddress)(lambda: None)
    app = api.as_fastapi()
    client = client_for(app)

    r = client.get("/user?name=foo&city=Boston")
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "foo"
    assert data["address"]["city"] == "Boston"


def test_computed_from():
    """ComputedFrom computes field from other output fields."""

    class UserWithFullName(BaseModel):
        first: Annotated[str, FromInput("first")]
        last: Annotated[str, FromInput("last")]
        full: Annotated[str, ComputedFrom(("first", "last"), lambda a, b: f"{a} {b}")]

    class QueryWithNames(BaseModel):
        first: str = "John"
        last: str = "Doe"

    api = SemblanceAPI()
    api.get("/user", input=QueryWithNames, output=UserWithFullName)(lambda: None)
    app = api.as_fastapi()
    client = client_for(app)

    r = client.get("/user?first=Jane&last=Smith")
    assert r.status_code == 200
    data = r.json()
    assert data["first"] == "Jane"
    assert data["last"] == "Smith"
    assert data["full"] == "Jane Smith"


def test_filter_by():
    """filter_by filters list items to those matching input field."""

    class UserWithStatus(BaseModel):
        name: Annotated[str, FromInput("name")]
        status: Annotated[str, FromInput("status")]

    class QueryWithStatus(BaseModel):
        name: str = "alice"
        status: str = "active"

    api = SemblanceAPI()
    api.get(
        "/users",
        input=QueryWithStatus,
        output=list[UserWithStatus],
        list_count=3,
        filter_by="status",
    )(lambda: None)
    app = api.as_fastapi()
    client = client_for(app)

    r = client.get("/users?name=x&status=active")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) <= 3
    for item in data:
        assert item["status"] == "active"


def test_stateful_mode():
    """Stateful mode: POST creates and stores; GET returns stored."""

    class CreateUser(BaseModel):
        name: str

    class UserWithId(BaseModel):
        id: str = ""
        name: Annotated[str, FromInput("name")]

    api = SemblanceAPI(stateful=True)
    api.post("/users", input=CreateUser, output=UserWithId)(lambda: None)
    api.get("/users", input=CreateUser, output=list[UserWithId])(lambda: None)
    app = api.as_fastapi()
    client = client_for(app)

    api.clear_store("/users")

    r1 = client.post("/users", json={"name": "alice"})
    assert r1.status_code == 200
    u1 = r1.json()
    assert u1["name"] == "alice"
    assert "id" in u1 and u1["id"]

    r2 = client.get("/users?name=x")
    assert r2.status_code == 200
    data = r2.json()
    assert len(data) == 1
    assert data[0]["name"] == "alice"
    assert data[0]["id"] == u1["id"]

    r3 = client.post("/users", json={"name": "bob"})
    assert r3.status_code == 200

    r4 = client.get("/users?name=x")
    assert r4.status_code == 200
    data4 = r4.json()
    assert len(data4) == 2
