"""
Run all documentation examples and print real outputs.
Used to verify examples work and capture output for docs.
"""

import json
import sys

sys.path.insert(0, "src")

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


def main():
    examples = [
        ("quick_start", example_quick_start),
        ("when_input", example_when_input),
        ("computed_from", example_computed_from),
        ("nested_model", example_nested_model),
        ("pagination", example_pagination),
        ("stateful", example_stateful),
    ]
    results = {}
    for name, fn in examples:
        try:
            results[name] = fn()
        except Exception as e:
            results[name] = {"error": str(e)}
    print(json.dumps(results, indent=2, default=str))


if __name__ == "__main__":
    main()
