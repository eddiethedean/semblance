"""Tests for SemblanceAPI core HTTP: GET, POST, seeding, headers/cookies."""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel

from semblance import FromCookie, FromHeader, FromInput, SemblanceAPI
from semblance.testing import test_client as make_client
from tests.example_models import User, UserQuery


def test_import_public_api_and_build_app():
    """Public symbols are importable and a minimal app builds and runs."""
    from semblance import SemblanceAPI
    from semblance.testing import test_client as client_for

    class Query(BaseModel):
        name: str = "x"

    class Item(BaseModel):
        name: str = ""

    api = SemblanceAPI()
    api.get("/items", input=Query, output=list[Item], list_count=1)(lambda: None)
    app = api.as_fastapi()
    client = client_for(app)
    r = client.get("/items?name=smoke")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_as_fastapi_returns_app(users_api):
    app = users_api.as_fastapi()
    assert app is not None
    routes = [r.path for r in app.routes if hasattr(r, "path")]
    assert "/users" in routes
    assert "/user" in routes


def test_get_users_returns_list(users_api):
    client = make_client(users_api.as_fastapi())
    r = client.get("/users?name=testuser")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 2
    for item in data:
        assert item["name"] == "testuser"
        assert "created_at" in item


def test_get_user_single_returns_one(users_api):
    client = make_client(users_api.as_fastapi())
    r = client.get("/user?name=solo")
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "solo"
    assert "created_at" in data


def test_date_range_respects_bounds(users_api):
    client = make_client(users_api.as_fastapi())
    r = client.get("/user?name=x&start_date=2024-06-01&end_date=2024-06-30")
    assert r.status_code == 200
    created = datetime.fromisoformat(r.json()["created_at"].replace("Z", "+00:00"))
    start = datetime(2024, 6, 1)
    end = datetime(2024, 6, 30, 23, 59, 59)
    assert start <= created.replace(tzinfo=None) <= end


def test_seed_from_non_numeric_field_is_ignored():
    """Non-int seed_from values are ignored; request still succeeds."""
    api = SemblanceAPI()
    api.get(
        "/users", input=UserQuery, output=list[User], list_count=2, seed_from="name"
    )(lambda: None)
    client = make_client(api.as_fastapi())
    assert client.get("/users?name=foo").status_code == 200


def test_seed_from_numeric_field():
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
    client = make_client(api.as_fastapi())
    r1 = client.get("/items?name=a&seed=100")
    r2 = client.get("/items?name=a&seed=100")
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json() == r2.json()


def test_api_seed_takes_precedence_over_seed_from():
    api = SemblanceAPI(seed=999)
    api.get(
        "/users",
        input=UserQuery,
        output=list[User],
        list_count=2,
        seed_from="name",
    )(lambda: None)
    client = make_client(api.as_fastapi())
    r1 = client.get("/users?name=a")
    r2 = client.get("/users?name=b")
    assert r1.status_code == 200 and r2.status_code == 200
    d1, d2 = r1.json(), r2.json()
    assert len(d1) == len(d2) == 2
    assert [x["created_at"] for x in d1] == [x["created_at"] for x in d2]


def test_list_count_from_input_field():
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
    client = make_client(api.as_fastapi())
    r = client.get("/users?name=a&n=4")
    assert r.status_code == 200
    assert len(r.json()) == 4


def test_list_count_fallback_when_field_invalid():
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
    client = make_client(api.as_fastapi())
    r = client.get("/users?name=x&limit=abc")
    assert r.status_code == 200
    assert len(r.json()) == 5


def test_deterministic_seed():
    api = SemblanceAPI(seed=42)
    api.get("/users", input=UserQuery, output=list[User], list_count=2)(lambda: None)
    client = make_client(api.as_fastapi())
    r1 = client.get("/users?name=seed")
    r2 = client.get("/users?name=seed")
    assert r1.status_code == 200 and r2.status_code == 200
    d1 = r1.json()
    d2 = r2.json()
    assert d1[0]["created_at"] == d2[0]["created_at"]
    assert d1[1]["created_at"] == d2[1]["created_at"]


def test_clear_store_stateful_api():
    class CreateReq(BaseModel):
        name: str = "x"

    class Item(BaseModel):
        id: str = ""
        name: str

    api = SemblanceAPI(stateful=True)
    api.get("/items", input=CreateReq, output=list[Item])(lambda: None)
    api.post("/items", input=CreateReq, output=Item)(lambda: None)
    client = make_client(api.as_fastapi())
    client.post("/items", json={"name": "a"})
    assert len(client.get("/items?name=x").json()) == 1
    api.clear_store("/items")
    assert len(client.get("/items?name=x").json()) == 0


def test_from_header_binding():
    class Query(BaseModel):
        name: str = "x"

    class Out(BaseModel):
        name: Annotated[str, FromInput("name")]
        request_id: Annotated[str, FromHeader("X-Request-Id")]

    api = SemblanceAPI()
    api.get("/echo", input=Query, output=Out)(lambda: None)
    client = make_client(api.as_fastapi())
    r = client.get("/echo?name=alice", headers={"X-Request-Id": "req-789"})
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "alice"
    assert data["request_id"] == "req-789"


def test_from_cookie_binding():
    class Query(BaseModel):
        name: str = "x"

    class Out(BaseModel):
        name: Annotated[str, FromInput("name")]
        session: Annotated[str, FromCookie("session_id")]

    api = SemblanceAPI()
    api.get("/echo", input=Query, output=Out)(lambda: None)
    client = make_client(api.as_fastapi())
    client.cookies.set("session_id", "sess-abc")
    r = client.get("/echo?name=bob")
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "bob"
    assert data["session"] == "sess-abc"


class CreateUserRequest(BaseModel):
    name: str
    start_date: str = "2020-01-01"
    end_date: str = "2025-12-31"


class UserGetInput(BaseModel):
    id: str = ""
    name: str = "alice"


def test_post_with_body():
    api = SemblanceAPI()
    api.post("/users", input=CreateUserRequest, output=User)(lambda: None)
    client = make_client(api.as_fastapi())
    r = client.post("/users", json={"name": "postuser"})
    assert r.status_code == 200
    assert r.json()["name"] == "postuser"


def test_get_with_path_param():
    api = SemblanceAPI()
    api.get("/users/{id}", input=UserGetInput, output=User)(lambda: None)
    client = make_client(api.as_fastapi())
    r = client.get("/users/user-123?name=pathuser")
    assert r.status_code == 200
    assert r.json()["name"] == "pathuser"


def test_post_with_path_param():
    class CreateUserWithId(BaseModel):
        id: str = ""
        name: str

    api = SemblanceAPI()
    api.post("/users/{id}", input=CreateUserWithId, output=User)(lambda: None)
    client = make_client(api.as_fastapi())
    r = client.post("/users/user-456", json={"name": "pathpost"})
    assert r.status_code == 200
    assert r.json()["name"] == "pathpost"


def test_post_with_seed_from_input():
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
    client = make_client(api.as_fastapi())
    body = {"name": "seedpost", "seed": 77}
    r1 = client.post("/users", json=body)
    r2 = client.post("/users", json=body)
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json()["created_at"] == r2.json()["created_at"]
