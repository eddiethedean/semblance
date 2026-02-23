"""Smoke test: import public API and build a minimal app.

Catches regressions in package exports and basic wiring.
"""

from pydantic import BaseModel

from semblance import (
    ComputedFrom,
    DateRangeFrom,
    FromInput,
    LinkProtocol,
    PageParams,
    PaginatedResponse,
    SemblanceAPI,
    WhenInput,
    register_link,
    test_client as make_client,
)


def test_import_public_api_and_build_app():
    """All public symbols are importable and a minimal app builds and runs."""
    class Query(BaseModel):
        name: str = "x"

    class Item(BaseModel):
        name: str = ""

    api = SemblanceAPI()
    api.get("/items", input=Query, output=list[Item], list_count=1)(lambda: None)
    app = api.as_fastapi()
    assert app is not None
    client = make_client(app)
    r = client.get("/items?name=smoke")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
