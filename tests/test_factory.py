"""Tests for semblance.factory - build_response, seed determinism, filter_by."""

from datetime import date
from typing import Annotated

import pytest
from pydantic import BaseModel

from semblance import FromInput
from semblance.factory import build_list, build_one, build_response
from tests.example_models import User, UserQuery


def test_build_one_with_seed_produces_deterministic_result():
    query = UserQuery(name="deterministic")
    r1 = build_one(User, UserQuery, query, seed=42)
    r2 = build_one(User, UserQuery, query, seed=42)
    assert r1.name == r2.name == "deterministic"
    assert r1.created_at == r2.created_at


def test_build_list_with_seed_produces_deterministic_results():
    query = UserQuery(name="list_seed")
    r1 = build_list(User, UserQuery, query, count=2, seed=99)
    r2 = build_list(User, UserQuery, query, count=2, seed=99)
    assert [u.name for u in r1] == [u.name for u in r2]
    assert [u.created_at for u in r1] == [u.created_at for u in r2]


def test_build_response_single_with_seed():
    query = UserQuery(name="single_seed")
    r1 = build_response(User, UserQuery, query, seed=123)
    r2 = build_response(User, UserQuery, query, seed=123)
    assert r1.name == r2.name == "single_seed"
    assert r1.created_at == r2.created_at


def test_build_response_invalid_single_model_raises():
    query = UserQuery(name="x")
    with pytest.raises(TypeError, match="Invalid output type"):
        build_response(int, UserQuery, query)


def test_build_response_list_output():
    query = UserQuery(name="list_test")
    result = build_response(list[User], UserQuery, query, list_count=3, seed=1)
    assert isinstance(result, list)
    assert len(result) == 3
    for item in result:
        assert item.name == "list_test"


def test_evaluate_overrides_callable_path():
    query = UserQuery(
        name="callable_test", start_date=date(2024, 1, 1), end_date=date(2024, 12, 31)
    )
    result = build_one(User, UserQuery, query)
    assert result.name == "callable_test"
    assert result.created_at is not None


def test_build_list_with_filter_by_on_generated_field():
    from typing import Literal

    class UserWithRole(BaseModel):
        name: Annotated[str, FromInput("name")]
        role: Literal["admin", "guest"]

    class QueryWithRole(BaseModel):
        name: str = "alice"
        role: str = "admin"

    query = QueryWithRole(name="alice", role="admin")
    result = build_list(
        UserWithRole, QueryWithRole, query, count=5, filter_by="role", seed=42
    )
    assert len(result) == 5
    for item in result:
        assert item.role == "admin"


def test_nested_list_of_models_builds():
    class Addr(BaseModel):
        city: str = "x"

    class WithAddrs(BaseModel):
        name: Annotated[str, FromInput("name")]
        addresses: list[Addr] = []

    query = UserQuery(name="nested-list")
    result = build_one(WithAddrs, UserQuery, query, seed=42)
    assert result.name == "nested-list"
    assert isinstance(result.addresses, list)


def test_computed_from_generated_sibling():
    from semblance import ComputedFrom

    class Out(BaseModel):
        name: Annotated[str, FromInput("name")]
        suffix: str
        label: Annotated[str, ComputedFrom(("name", "suffix"), lambda a, b: f"{a}-{b}")]

    query = UserQuery(name="ann")
    result = build_one(Out, UserQuery, query, seed=7)
    assert result.label == f"{result.name}-{result.suffix}"
