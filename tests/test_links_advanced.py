"""Tests for advanced link types: WhenInput, ComputedFrom, nested models, filter_by."""

from typing import Annotated

from pydantic import BaseModel

from semblance import ComputedFrom, FromInput, SemblanceAPI, WhenInput
from semblance.resolver import resolve_overrides
from semblance.testing import test_client as make_client


def test_when_input_condition_met_applies_link():
    class UserWithStatus(BaseModel):
        name: Annotated[str, FromInput("name")]
        status: Annotated[str, WhenInput("include_status", True, FromInput("status"))]

    class QueryWithStatus(BaseModel):
        name: str = "alice"
        status: str = "active"
        include_status: bool = False

    api = SemblanceAPI()
    api.get("/user", input=QueryWithStatus, output=UserWithStatus)(lambda: None)
    client = make_client(api.as_fastapi())
    r = client.get("/user?name=x&status=admin&include_status=true")
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "x"
    assert data["status"] == "admin"


def test_when_input_condition_not_met_uses_generated():
    class UserWithStatus(BaseModel):
        status: Annotated[str, WhenInput("include_status", True, FromInput("status"))]

    class QueryWithStatus(BaseModel):
        status: str = "active"
        include_status: bool = False

    overrides = resolve_overrides(UserWithStatus, QueryWithStatus, QueryWithStatus())
    assert "status" not in overrides


def test_nested_model_linking():
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
    client = make_client(api.as_fastapi())
    r = client.get("/user?name=foo&city=Boston")
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "foo"
    assert data["address"]["city"] == "Boston"


def test_computed_from():
    class UserWithFullName(BaseModel):
        first: Annotated[str, FromInput("first")]
        last: Annotated[str, FromInput("last")]
        full: Annotated[str, ComputedFrom(("first", "last"), lambda a, b: f"{a} {b}")]

    class QueryWithNames(BaseModel):
        first: str = "John"
        last: str = "Doe"

    api = SemblanceAPI()
    api.get("/user", input=QueryWithNames, output=UserWithFullName)(lambda: None)
    client = make_client(api.as_fastapi())
    r = client.get("/user?first=Jane&last=Smith")
    assert r.status_code == 200
    data = r.json()
    assert data["first"] == "Jane"
    assert data["last"] == "Smith"
    assert data["full"] == "Jane Smith"


def test_filter_by_filters_generated_field():
    """filter_by must constrain a generated field, not a FromInput-bound one."""
    from typing import Literal

    class Query(BaseModel):
        name: str = "alice"
        role: str = "admin"

    class User(BaseModel):
        name: Annotated[str, FromInput("name")]
        role: Literal["admin", "guest"]

    api = SemblanceAPI(seed=42)
    api.get(
        "/users",
        input=Query,
        output=list[User],
        list_count=5,
        filter_by="role",
    )(lambda: None)
    client = make_client(api.as_fastapi())
    r = client.get("/users?name=x&role=admin")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 5
    assert all(item["role"] == "admin" for item in data)
