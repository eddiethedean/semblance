"""Unit tests for semblance.export helpers and integration."""

import json
import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI
from fastapi.responses import Response
from pydantic import BaseModel
from starlette.testclient import TestClient

from semblance import FromInput, SemblanceAPI
from semblance.export import (
    _get_routes,
    export_fixtures,
    export_openapi,
)


def test_get_routes_returns_path_method_route_id():
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    @app.get("/users")
    def get_users():
        return []

    @app.post("/items")
    def create_item():
        return {}

    routes = _get_routes(app)
    assert ("/users", "GET", "users_GET") in routes
    assert ("/items", "POST", "items_POST") in routes


def test_get_routes_path_with_params():
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    @app.get("/users/{id}")
    def get_user():
        return {}

    routes = _get_routes(app)
    assert len(routes) == 1
    path, method, route_id = routes[0]
    assert path == "/users/{id}"
    assert method == "GET"
    assert route_id == "users_id_GET"


def test_get_routes_excludes_head_options():
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    @app.get("/x")
    def x():
        return {}

    methods = {m for _, m, _ in _get_routes(app)}
    assert "HEAD" not in methods
    assert "OPTIONS" not in methods


def test_export_openapi_empty_app():
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    schema = export_openapi(app)
    assert schema.get("paths") == {}


def test_export_fixtures_empty_app(tmp_path):
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    export_fixtures(app, tmp_path)
    assert (tmp_path / "openapi.json").exists()
    assert len(list(tmp_path.glob("*.json"))) == 1


def test_export_openapi_include_examples():
    from semblance.cli import _load_app

    app = _load_app("tests.sample_app:app")
    schema = export_openapi(app, include_examples=True)
    json_content = schema["paths"]["/users"]["get"]["responses"]["200"]["content"][
        "application/json"
    ]
    assert "example" in json_content
    assert isinstance(json_content["example"], list)


def test_export_fixtures_includes_post_endpoint():
    class CreateReq(BaseModel):
        name: str = "fixture"

    class Item(BaseModel):
        name: Annotated[str, FromInput("name")]

    api = SemblanceAPI()
    api.post("/items", input=CreateReq, output=Item)(lambda: None)
    with tempfile.TemporaryDirectory() as tmp:
        export_fixtures(api.as_fastapi(), tmp)
        data = json.loads((Path(tmp) / "items_POST.json").read_text())
        assert data["name"] == "fixture"


def test_export_openapi_skips_example_when_endpoint_returns_422():
    class StrictBody(BaseModel):
        required_field: str

    class Out(BaseModel):
        value: str = "ok"

    api = SemblanceAPI()
    api.post("/strict", input=StrictBody, output=Out)(lambda: None)
    schema = export_openapi(api.as_fastapi(), include_examples=True)
    responses = schema["paths"]["/strict"]["post"].get("responses", {})
    content = responses.get("200", {}).get("content", {})
    assert "example" not in content.get("application/json", {})


def test_export_fixtures_delete_204(tmp_path):
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    @app.delete("/items/{id}", status_code=204)
    def delete_item(id: int):
        return Response(status_code=204)

    export_fixtures(app, tmp_path)
    delete_files = list(tmp_path.glob("*DELETE.json"))
    assert delete_files
    payload = json.loads(delete_files[0].read_text())
    assert payload.get("status") == 204


def test_export_does_not_fabricate_204_for_failed_delete(tmp_path):
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    @app.delete("/protected/{id}")
    def delete_protected(id: int):
        status_code = {1: 401, 2: 404, 3: 500}[id]
        return Response(status_code=status_code)

    client = TestClient(app)
    assert [client.delete(f"/protected/{id}").status_code for id in (1, 2, 3)] == [
        401,
        404,
        500,
    ]

    export_fixtures(app, tmp_path)

    assert not (tmp_path / "protected_id_DELETE.json").exists()
    responses = export_openapi(app, include_examples=True)["paths"]["/protected/{id}"][
        "delete"
    ]["responses"]
    assert "204" not in responses
