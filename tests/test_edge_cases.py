"""Edge-case and error-path tests."""

from typing import Annotated

import pytest
from pydantic import BaseModel

from semblance import SemblanceAPI, test_client as client_for
from semblance.factory import build_response

from tests.example_models import User, UserQuery


def test_import_semblance_without_pytest():
    """semblance can be imported without pytest installed (no dev deps)."""
    import semblance  # noqa: F401

    from semblance import SemblanceAPI, test_client

    assert SemblanceAPI is not None
    assert test_client is not None


def test_build_response_invalid_output_raises():
    """build_response with invalid output type raises helpful TypeError."""
    query = UserQuery(name="x")
    with pytest.raises(TypeError, match="Invalid output type"):
        build_response(str, UserQuery, query)

    with pytest.raises(TypeError, match="Invalid output type"):
        build_response(list, UserQuery, query)  # bare list, no args


def test_query_validation_returns_422(api):
    """Invalid query params (e.g. bad date format) return 422."""
    client = client_for(api.as_fastapi())
    r = client.get("/user?name=x&start_date=not-a-date")
    assert r.status_code == 422


def test_duplicate_path_raises():
    """Registering the same GET path twice raises ValueError when building the app."""
    api = SemblanceAPI()
    api.get("/users", input=UserQuery, output=list[User])(lambda: None)
    api.get("/users", input=UserQuery, output=list[User])(lambda: None)
    with pytest.raises(ValueError, match="Duplicate GET endpoint"):
        api.as_fastapi()


@pytest.fixture
def api():
    api = SemblanceAPI()
    api.get("/users", input=UserQuery, output=list[User], list_count=2)(lambda: None)
    api.get("/user", input=UserQuery, output=User)(lambda: None)
    return api


class OptionalQuery(BaseModel):
    """Query with optional name for testing FromInput(None) behavior."""

    name: str | None = None


def test_from_input_with_none_uses_generated():
    """When FromInput target is None, no override is applied; Polyfactory generates the value."""
    from semblance.links import FromInput
    from semblance.resolver import resolve_overrides

    class OutputWithFromInput(BaseModel):
        name: Annotated[str, FromInput("name")]

    overrides = resolve_overrides(OutputWithFromInput, OptionalQuery, OptionalQuery())
    assert "name" not in overrides
