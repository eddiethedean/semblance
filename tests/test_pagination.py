"""Tests for PaginatedResponse and pagination helpers."""

from typing import Annotated

from pydantic import BaseModel

from semblance import FromInput, PageParams, PaginatedResponse, SemblanceAPI
from semblance.factory import build_response
from semblance.testing import test_client as make_client
from tests.example_models import User


class UserListQuery(PageParams, BaseModel):
    name: str = "alice"


def test_paginated_response_offset_zero():
    """offset=0, limit=3: total equals pool size and items length."""
    api = SemblanceAPI(seed=42)
    api.get("/users", input=UserListQuery, output=PaginatedResponse[User])(lambda: None)
    client = make_client(api.as_fastapi())
    r = client.get("/users?name=paged&limit=3&offset=0")
    assert r.status_code == 200
    data = r.json()
    assert data["limit"] == 3
    assert data["offset"] == 0
    assert data["total"] == 3
    assert len(data["items"]) == 3


def test_paginated_response_with_offset():
    """offset=10, limit=5: total is simulated pool size before slicing."""
    api = SemblanceAPI(seed=42)
    api.get("/users", input=UserListQuery, output=PaginatedResponse[User])(lambda: None)
    client = make_client(api.as_fastapi())
    r = client.get("/users?name=paged&limit=5&offset=10")
    assert r.status_code == 200
    data = r.json()
    assert data["limit"] == 5
    assert data["offset"] == 10
    assert data["total"] == 15
    assert len(data["items"]) == 5


def test_pagination_limit_offset_fallback_on_invalid_limit():
    """Pagination uses fallback when limit cannot be coerced to int."""

    class BadLimitQuery(BaseModel):
        limit: str = "not-a-number"
        offset: int = 0
        name: str = "x"

    result = build_response(
        PaginatedResponse[User],
        BadLimitQuery,
        BadLimitQuery(),
        seed=1,
    )
    assert result.limit == 10
    assert result.offset == 0
    assert result.total == 10
    assert len(result.items) == 10


def test_pagination_limit_offset_fallback_on_invalid_offset():
    """Pagination uses fallback when offset cannot be coerced to int."""

    class BadOffsetQuery(BaseModel):
        limit: int = 5
        offset: str = "invalid"
        name: str = "x"

    result = build_response(
        PaginatedResponse[User],
        BadOffsetQuery,
        BadOffsetQuery(),
        seed=1,
    )
    assert result.limit == 5
    assert result.offset == 0
    assert result.total == 5
    assert len(result.items) == 5


def test_paginated_filter_by_short_pool():
    """When filter_by undershoots, total reflects actual pool size."""

    class UserWithRole(BaseModel):
        name: Annotated[str, FromInput("name")]
        role: str

    class QueryWithRole(BaseModel):
        name: str = "x"
        role: str = "rare_role_xyz"
        limit: int = 5
        offset: int = 12

    result = build_response(
        PaginatedResponse[UserWithRole],
        QueryWithRole,
        QueryWithRole(),
        seed=1,
        filter_by="role",
    )
    assert result.total <= 17
    assert len(result.items) <= result.limit
    if result.total > result.offset:
        assert len(result.items) == min(result.limit, result.total - result.offset)
    else:
        assert len(result.items) == 0


def test_build_response_paginated_with_filter_by():
    """Paginated filter_by returns items matching filter field."""

    class UserWithStatus(BaseModel):
        name: Annotated[str, FromInput("name")]
        status: Annotated[str, FromInput("status")]

    class QueryWithStatus(BaseModel):
        name: str = "x"
        status: str = "active"
        limit: int = 5
        offset: int = 0

    query = QueryWithStatus(name="alice", status="active", limit=3, offset=0)
    result = build_response(
        PaginatedResponse[UserWithStatus],
        QueryWithStatus,
        query,
        seed=1,
        filter_by="status",
    )
    assert result.limit == 3
    assert result.offset == 0
    assert result.total == 3
    assert len(result.items) == 3
    for item in result.items:
        assert item.status == "active"
