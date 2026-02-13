"""
Run all documentation examples and print real outputs.
Used to verify examples work and capture output for docs.

Run from project root: python docs/guides/examples/run_examples.py
"""

import json
import sys
from pathlib import Path

# Project root (parent of docs/guides/examples/)
_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_root / "src"))
sys.path.insert(0, str(_root))

from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel

from semblance import (
    ComputedFrom,
    DateRangeFrom,
    FromInput,
    PageParams,
    PaginatedResponse,
    SemblanceAPI,
    WhenInput,
    test_client,
)


def example_quick_start():
    """README / Getting Started quick start."""

    class UserQuery(BaseModel):
        name: str = "alice"
        start_date: date = date(2020, 1, 1)
        end_date: date = date(2025, 12, 31)

    class User(BaseModel):
        name: Annotated[str, FromInput("name")]
        created_at: Annotated[
            datetime,
            DateRangeFrom("start_date", "end_date"),
        ]

    api = SemblanceAPI(seed=42)
    api.get("/users", input=UserQuery, output=list[User], list_count=2)(lambda: None)
    app = api.as_fastapi()
    client = test_client(app)
    r = client.get("/users?name=alice&start_date=2024-01-01&end_date=2024-12-31")
    return r.json()


def example_when_input():
    """Advanced Links: WhenInput."""

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
    client = test_client(app)
    r = client.get("/user?name=x&status=admin&include_status=true")
    return r.json()


def example_computed_from():
    """Advanced Links: ComputedFrom."""

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
    client = test_client(app)
    r = client.get("/user?first=Jane&last=Smith")
    return r.json()


def example_nested_model():
    """Advanced Links: Nested model."""

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
    client = test_client(app)
    r = client.get("/user?name=alice&city=Boston")
    return r.json()


def example_pagination():
    """Pagination: PageParams, PaginatedResponse."""

    class User(BaseModel):
        name: Annotated[str, FromInput("name")]

    class UserListQuery(PageParams, BaseModel):
        name: str = "alice"

    api = SemblanceAPI(seed=1)
    api.get("/users", input=UserListQuery, output=PaginatedResponse[User])(lambda: None)
    app = api.as_fastapi()
    client = test_client(app)
    r = client.get("/users?name=alice&limit=3&offset=0")
    return r.json()


def example_filter_by():
    """Simulation Options: filter_by."""

    class UserWithStatus(BaseModel):
        name: Annotated[str, FromInput("name")]
        status: Annotated[str, FromInput("status")]

    class QueryWithStatus(BaseModel):
        name: str = "alice"
        status: str = "active"

    api = SemblanceAPI(seed=1)
    api.get(
        "/users",
        input=QueryWithStatus,
        output=list[UserWithStatus],
        list_count=3,
        filter_by="status",
    )(lambda: None)
    app = api.as_fastapi()
    client = test_client(app)
    r = client.get("/users?name=x&status=active")
    return r.json()


def example_error_rate_success():
    """Simulation Options: error_rate=0 (always success)."""

    class User(BaseModel):
        name: Annotated[str, FromInput("name")]

    class UserQuery(BaseModel):
        name: str = "alice"

    api = SemblanceAPI(seed=99)
    api.get(
        "/users",
        input=UserQuery,
        output=list[User],
        list_count=2,
        error_rate=0,
    )(lambda: None)
    app = api.as_fastapi()
    client = test_client(app)
    r = client.get("/users?name=alice")
    return r.json()


def example_plugins_from_env():
    """Plugins: FromEnv custom link."""

    class FromEnv:
        def __init__(self, env_var: str):
            self.env_var = env_var

        def resolve(self, input_data: dict, rng):
            import os
            return os.environ.get(self.env_var)

    from semblance import register_link

    register_link(FromEnv)

    class User(BaseModel):
        name: Annotated[str, FromEnv("USER_NAME")]
        role: Annotated[str, FromInput("role")]

    class UserQuery(BaseModel):
        role: str = "viewer"

    api = SemblanceAPI(seed=42)
    api.get("/user", input=UserQuery, output=User)(lambda: None)
    app = api.as_fastapi()
    client = test_client(app)
    import os
    os.environ["USER_NAME"] = "DocBot"
    try:
        r = client.get("/user?role=admin")
        return r.json()
    finally:
        os.environ.pop("USER_NAME", None)


def example_plugins_random_choice():
    """Plugins: RandomChoice custom link."""

    class RandomChoice:
        def __init__(self, field: str):
            self.field = field

        def resolve(self, input_data: dict, rng):
            opts = input_data.get(self.field)
            if opts and isinstance(opts, (list, tuple)):
                return rng.choice(opts)
            return None

    from semblance import register_link

    register_link(RandomChoice)

    class Item(BaseModel):
        choice: Annotated[str, RandomChoice("options")]

    class QueryWithOptions(BaseModel):
        options: list[str] = ["a", "b", "c"]

    api = SemblanceAPI(seed=42)
    api.get("/item", input=QueryWithOptions, output=Item)(lambda: None)
    app = api.as_fastapi()
    client = test_client(app)
    r = client.get("/item?options=a&options=b&options=c")
    return r.json()


def example_stateful():
    """Stateful mode."""

    class CreateUser(BaseModel):
        name: str

    class UserWithId(BaseModel):
        id: str = ""
        name: Annotated[str, FromInput("name")]

    api = SemblanceAPI(stateful=True)
    api.post("/users", input=CreateUser, output=UserWithId)(lambda: None)
    api.get("/users", input=CreateUser, output=list[UserWithId])(lambda: None)
    app = api.as_fastapi()
    client = test_client(app)
    api.clear_store("/users")
    r1 = client.post("/users", json={"name": "alice"})
    r2 = client.post("/users", json={"name": "bob"})
    r3 = client.get("/users?name=x")
    return {"create_alice": r1.json(), "create_bob": r2.json(), "list": r3.json()}


def example_doc_basic():
    """docs/examples/basic.md - load from examples.basic.app."""
    from examples.basic.app import app

    client = test_client(app)
    r = client.get("/users?name=alice&start_date=2024-01-01&end_date=2024-12-31")
    return r.json()


def example_doc_pagination():
    """docs/examples/pagination.md - load from examples.pagination.app."""
    from examples.pagination.app import app

    client = test_client(app)
    r = client.get("/users?limit=3&offset=0&name=alice")
    return r.json()


def example_doc_nested():
    """docs/examples/nested.md - load from examples.nested.app."""
    from examples.nested.app import app

    client = test_client(app)
    r = client.get("/user?name=foo&city=Boston")
    return r.json()


def example_doc_stateful():
    """docs/examples/stateful.md - load from examples.stateful.app."""
    from examples.stateful.app import app, api

    client = test_client(app)
    api.clear_store("/users")
    r1 = client.post("/users", json={"name": "alice"})
    r2 = client.post("/users", json={"name": "bob"})
    r3 = client.get("/users?name=x")
    return {"post_alice": r1.json(), "post_bob": r2.json(), "get_list": r3.json()}


def example_doc_advanced():
    """docs/examples/advanced.md - load from examples.advanced.app."""
    from examples.advanced.app import app

    client = test_client(app)
    r1 = client.get("/user/status?name=alice&include_status=true&status=active")
    r2 = client.get("/user/fullname?first=Jane&last=Smith")
    r3 = client.get("/users?name=x&status=active&include_status=true")
    return {"status": r1.json(), "fullname": r2.json(), "users": r3.json()}


def example_doc_error_simulation():
    """docs/examples/error_simulation.md - load from examples.error_simulation.app."""
    from examples.error_simulation.app import app

    client = test_client(app)
    successes = []
    for _ in range(10):
        r = client.get("/users?name=alice")
        if r.status_code == 200:
            successes.append(r.json())
            break
    return successes[0] if successes else {"note": "all requests failed (error_rate)"}


def example_doc_plugins():
    """docs/examples/plugins.md - load from examples.plugins.app with USER_NAME."""
    import os

    os.environ["USER_NAME"] = "DocBot"
    try:
        from examples.plugins.app import app

        client = test_client(app)
        r = client.get("/user?role=admin")
        return r.json()
    finally:
        os.environ.pop("USER_NAME", None)


EXAMPLES = [
    ("quick_start", example_quick_start),
    ("when_input", example_when_input),
    ("computed_from", example_computed_from),
    ("nested_model", example_nested_model),
    ("pagination", example_pagination),
    ("filter_by", example_filter_by),
    ("error_rate_success", example_error_rate_success),
    ("plugins_from_env", example_plugins_from_env),
    ("plugins_random_choice", example_plugins_random_choice),
    ("stateful", example_stateful),
    # docs/examples/*.md - run actual example apps
    ("doc_basic", example_doc_basic),
    ("doc_pagination", example_doc_pagination),
    ("doc_nested", example_doc_nested),
    ("doc_stateful", example_doc_stateful),
    ("doc_advanced", example_doc_advanced),
    ("doc_error_simulation", example_doc_error_simulation),
    ("doc_plugins", example_doc_plugins),
]


def main():
    examples = EXAMPLES
    results = {}
    for name, fn in examples:
        try:
            results[name] = fn()
        except Exception as e:
            results[name] = {"error": str(e)}
    print(json.dumps(results, indent=2, default=str))


if __name__ == "__main__":
    main()
