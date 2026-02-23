"""Tests for Phase 7: Mount, middleware, config, request links, pytest plugin, reproducible failures."""

import pytest

from semblance import SemblanceAPI
from semblance.config import load_config
from semblance.testing import test_client as make_client
from tests.example_models import User, UserQuery

# --- Mount ---


def test_mount_into_prefix():
    """mount_into makes Semblance routes available under path_prefix."""
    from fastapi import FastAPI

    api = SemblanceAPI()
    api.get("/users", input=UserQuery, output=list[User], list_count=1)(lambda: None)
    parent = FastAPI()
    api.mount_into(parent, "/api")
    client = make_client(parent)
    r = client.get("/api/users?name=alice")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["name"] == "alice"


def test_mount_into_root():
    """mount_into with path_prefix '/' mounts at root (same as as_fastapi)."""
    from fastapi import FastAPI

    api = SemblanceAPI()
    api.get("/items", input=UserQuery, output=list[User], list_count=1)(lambda: None)
    parent = FastAPI()
    api.mount_into(parent, "/")
    client = make_client(parent)
    r = client.get("/items?name=x")
    assert r.status_code == 200


# --- Middleware ---


def test_add_middleware_adds_header():
    """add_middleware applies middleware; response has middleware-added header."""
    from starlette.middleware.base import BaseHTTPMiddleware

    class AddHeaderMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            response = await call_next(request)
            response.headers["X-Semblance-Test"] = "ok"
            return response

    api = SemblanceAPI()
    api.get("/users", input=UserQuery, output=list[User], list_count=1)(lambda: None)
    api.add_middleware(AddHeaderMiddleware)
    app = api.as_fastapi()
    client = make_client(app)
    r = client.get("/users?name=x")
    assert r.status_code == 200
    assert r.headers.get("X-Semblance-Test") == "ok"


# --- Config ---


def test_load_config_from_yaml(tmp_path):
    """load_config reads seed and validate_responses from semblance.yaml."""
    yaml_path = tmp_path / "semblance.yaml"
    yaml_path.write_text("seed: 99\nvalidate_responses: true\n")
    cfg = load_config(yaml_path)
    assert cfg.seed == 99
    assert cfg.validate_responses is True


def test_load_config_from_pyproject_toml(tmp_path):
    """load_config reads [tool.semblance] from pyproject.toml when available."""
    toml_path = tmp_path / "pyproject.toml"
    toml_path.write_text(
        '[project]\nname = "test"\n\n[tool.semblance]\nseed = 42\nstateful = true\n'
    )
    cfg = load_config(toml_path)
    assert cfg.seed == 42
    assert cfg.stateful is True


def test_semblance_api_uses_config_path(tmp_path):
    """SemblanceAPI(config_path=...) applies config defaults."""
    yaml_path = tmp_path / "semblance.yaml"
    yaml_path.write_text("seed: 123\nvalidate_responses: true\n")
    api = SemblanceAPI(config_path=str(yaml_path))
    api.get("/users", input=UserQuery, output=list[User], list_count=2)(lambda: None)
    client = make_client(api.as_fastapi())
    r1 = client.get("/users?name=a")
    r2 = client.get("/users?name=a")
    assert r1.status_code == 200 and r2.status_code == 200
    # Same seed => same list order/content
    assert r1.json() == r2.json()


def test_semblance_api_from_config(tmp_path):
    """SemblanceAPI.from_config() builds API with config defaults."""
    yaml_path = tmp_path / "semblance.yaml"
    yaml_path.write_text("seed: 456\n")
    api = SemblanceAPI.from_config(str(yaml_path))
    api.get("/items", input=UserQuery, output=list[User], list_count=1)(lambda: None)
    client = make_client(api.as_fastapi())
    r = client.get("/items?name=x")
    assert r.status_code == 200


# --- Pytest plugin ---


@pytest.mark.semblance(app="tests.sample_app:api")
def test_pytest_plugin_semblance_client(semblance_client):
    """Plugin provides semblance_client when test is marked with semblance(app=...)."""
    r = semblance_client.get("/users?name=plugin_test")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["name"] == "plugin_test"


@pytest.mark.semblance_property_tests(app="tests.sample_app:api")
def test_semblance_property_per_endpoint(
    semblance_client,
    semblance_api,
    endpoint_path,
    endpoint_method,
):
    """Plugin parametrizes by endpoint; run property test for each (path, method)."""
    spec = semblance_api.get_spec(endpoint_path, endpoint_method)
    assert spec is not None
    if spec.output_annotation is None:
        pytest.skip("DELETE with no output model")
    from semblance.property_testing import strategy_for_input_model, test_endpoint

    strategy = strategy_for_input_model(spec.input_model)
    test_endpoint(
        semblance_client,
        endpoint_method,
        endpoint_path,
        strategy,
        spec.output_annotation,
        validate_response=True,
    )
