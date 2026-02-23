"""
Pytest plugin for Semblance: fixtures and optional property-test generation.

Use @pytest.mark.semblance(app="module:attr") to inject semblance_api and
semblance_client fixtures. Use @pytest.mark.semblance_property_tests(app="...")
with test_semblance_property_per_endpoint to run property tests per endpoint.
"""

from __future__ import annotations

import importlib.util
import sys
from typing import Any

import pytest


def _load_semblance_api(app_path: str) -> Any:
    """Load SemblanceAPI from module:attr path."""
    if ":" not in app_path:
        raise ValueError(
            f"Invalid app path {app_path!r}. Use module:attr (e.g. app:api)."
        )
    module_path, attr = app_path.split(":", 1)
    if not module_path or not attr:
        raise ValueError("module:attr must both be non-empty")
    spec = importlib.util.find_spec(module_path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Module {module_path!r} not found")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_path] = module
    spec.loader.exec_module(module)
    if not hasattr(module, attr):
        raise ValueError(f"Attribute {attr!r} not found in module {module_path!r}")
    app = getattr(module, attr)
    if hasattr(app, "as_fastapi"):
        return app
    raise ValueError(f"{attr!r} is not a SemblanceAPI (no as_fastapi)")


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "semblance(app=str): Load SemblanceAPI from module:attr for semblance_api/semblance_client fixtures.",
    )
    config.addinivalue_line(
        "markers",
        "semblance_property_tests(app=str): Parametrize test with (path, method) for each endpoint.",
    )


def _get_app_path_from_marker(request: pytest.FixtureRequest) -> str | None:
    """Get app path from semblance or semblance_property_tests marker."""
    for name in ("semblance", "semblance_property_tests"):
        marker = request.node.get_closest_marker(name)
        if marker is not None:
            app_path = marker.kwargs.get("app") or (
                marker.args[0] if marker.args else None
            )
            if isinstance(app_path, str):
                return app_path
    return None


@pytest.fixture
def semblance_api(request: pytest.FixtureRequest) -> Any:
    """Yield the SemblanceAPI instance from the test's semblance marker."""
    app_path = _get_app_path_from_marker(request)
    if not app_path:
        pytest.skip(
            "Test is not marked with @pytest.mark.semblance(app='module:attr') "
            "or @pytest.mark.semblance_property_tests(app='module:attr')"
        )
    return _load_semblance_api(app_path)


@pytest.fixture
def semblance_client(semblance_api: Any) -> Any:
    """Yield a test client for the SemblanceAPI (requires semblance_api fixture)."""
    from semblance.testing import test_client

    return test_client(semblance_api.as_fastapi())


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Parametrize tests marked with semblance_property_tests by (path, method)."""
    marker = metafunc.definition.get_closest_marker("semblance_property_tests")
    if marker is None:
        return
    app_path = marker.kwargs.get("app") or (marker.args[0] if marker.args else None)
    if not app_path:
        return
    if (
        "endpoint_path" not in metafunc.fixturenames
        or "endpoint_method" not in metafunc.fixturenames
    ):
        return
    api = _load_semblance_api(app_path)
    specs = api.get_endpoint_specs()
    ids = []
    argvalues = []
    for spec in specs:
        for method in spec.methods:
            ids.append(f"{method}_{spec.path.replace('/', '_')}")
            argvalues.append((spec.path, method))
    metafunc.parametrize("endpoint_path,endpoint_method", argvalues, ids=ids)
