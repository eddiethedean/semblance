"""Edge-case and error-path tests."""

from typing import Annotated

import pytest
from pydantic import BaseModel

from semblance.factory import build_response
from semblance.links import FromInput
from semblance.resolver import resolve_overrides
from semblance.testing import test_client as make_client
from tests.example_models import UserQuery


def test_build_response_invalid_output_raises():
    query = UserQuery(name="x")
    with pytest.raises(TypeError, match="Invalid output type"):
        build_response(str, UserQuery, query)
    with pytest.raises(TypeError, match="Invalid output type"):
        build_response(list, UserQuery, query)


def test_query_validation_returns_422(users_api):
    client = make_client(users_api.as_fastapi())
    r = client.get("/user?name=x&start_date=not-a-date")
    assert r.status_code == 422


class OptionalQuery(BaseModel):
    name: str | None = None


def test_from_input_with_none_uses_generated():
    class OutputWithFromInput(BaseModel):
        name: Annotated[str, FromInput("name")]

    overrides = resolve_overrides(OutputWithFromInput, OptionalQuery, OptionalQuery())
    assert "name" not in overrides
