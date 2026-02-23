"""Unit tests for semblance.export helpers and edge cases."""

import json

from fastapi import FastAPI

from semblance.export import (
    _fill_path_params,
    _get_routes,
    export_fixtures,
    export_openapi,
)


def test_fill_path_params_single_param():
    assert _fill_path_params("/users/{id}") == "/users/1"


def test_fill_path_params_multiple_params():
    assert _fill_path_params("/users/{id}/posts/{post_id}") == "/users/1/posts/1"


def test_fill_path_params_no_params():
    path = "/users"
    assert _fill_path_params(path) == path


def test_fill_path_params_root():
    assert _fill_path_params("/") == "/"


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

    routes = _get_routes(app)
    methods = {m for _, m, _ in routes}
    assert "HEAD" not in methods
    assert "OPTIONS" not in methods
    assert "GET" in methods


def test_get_routes_empty_app():
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    routes = _get_routes(app)
    assert routes == []


def test_export_openapi_empty_app():
    """export_openapi on app with no API routes returns schema with empty paths."""
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    schema = export_openapi(app)
    assert "paths" in schema
    assert schema["paths"] == {}


def test_export_fixtures_empty_app(tmp_path):
    """export_fixtures on app with no API routes writes only openapi.json."""
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    export_fixtures(app, tmp_path)
    openapi_file = tmp_path / "openapi.json"
    assert openapi_file.exists()
    schema = json.loads(openapi_file.read_text())
    assert schema.get("paths") == {}
    # No other JSON fixture files (only openapi.json)
    json_files = list(tmp_path.glob("*.json"))
    assert len(json_files) == 1
