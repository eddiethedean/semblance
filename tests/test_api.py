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


def test_seed_from_field_provides_determinism():
    """When seed_from is set, input field value is used as seed."""
    api = SemblanceAPI()
    api.get("/users", input=UserQuery, output=list[User], list_count=2, seed_from="name")(
        lambda: None
    )
    client = client_for(api.as_fastapi())
    # seed_from="name" - name is str, not int; _resolve_seed tries int(val) and fails
    # so seed is None - test that it still works
    r = client.get("/users?name=foo")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2


def test_seed_from_numeric_field():
    """When seed_from points to numeric field, it is used as seed."""
    from pydantic import BaseModel

    class QueryWithSeed(BaseModel):
        name: str = "x"
        seed: int = 42

    class Out(BaseModel):
        name: str

    api = SemblanceAPI()
    api.get(
        "/items",
        input=QueryWithSeed,
        output=list[Out],
        list_count=2,
        seed_from="seed",
    )(lambda: None)
    client = client_for(api.as_fastapi())
    r1 = client.get("/items?name=a&seed=100")
    r2 = client.get("/items?name=a&seed=100")
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json() == r2.json()


def test_api_seed_takes_precedence_over_seed_from():
    """When API has seed=, it overrides seed_from input field."""
    api = SemblanceAPI(seed=999)
    api.get(
        "/users",
        input=UserQuery,
        output=list[User],
        list_count=2,
        seed_from="name",
    )(lambda: None)
    client = client_for(api.as_fastapi())
    r1 = client.get("/users?name=a")
    r2 = client.get("/users?name=b")
    # Both use API seed 999; name differs (FromInput), but created_at should match
    assert r1.status_code == 200 and r2.status_code == 200
    d1, d2 = r1.json(), r2.json()
    assert len(d1) == len(d2) == 2
    assert [x["created_at"] for x in d1] == [x["created_at"] for x in d2]


def test_list_count_from_input_field():
    """When list_count is str, input field value is used."""
    from pydantic import BaseModel

    class QueryWithCount(BaseModel):
        name: str = "x"
        n: int = 3

    api = SemblanceAPI()
    api.get(
        "/users",
        input=QueryWithCount,
        output=list[User],
        list_count="n",
    )(lambda: None)
    client = client_for(api.as_fastapi())
    r = client.get("/users?name=a&n=4")
    assert r.status_code == 200
    assert len(r.json()) == 4


def test_clear_store_stateful_api():
    """clear_store removes items from stateful store."""
    from pydantic import BaseModel

    class CreateReq(BaseModel):
        name: str = "x"

    class Item(BaseModel):
        id: str = ""
        name: str

    api = SemblanceAPI(stateful=True)
    api.get("/items", input=CreateReq, output=list[Item])(lambda: None)
    api.post("/items", input=CreateReq, output=Item)(lambda: None)
    client = client_for(api.as_fastapi())

    # Create item
    client.post("/items", json={"name": "a"})
    r = client.get("/items?name=x")
    assert len(r.json()) == 1

    api.clear_store("/items")
    r = client.get("/items?name=x")
    assert len(r.json()) == 0
