"""
Export mocks for frontend integration.

Export OpenAPI schema (optionally with response examples from live calls) and
JSON fixtures per endpoint for MSW, fixtures, or OpenAPI-driven tooling.
"""

import json
import re
from pathlib import Path
from typing import Any, cast

from fastapi import FastAPI
from fastapi.testclient import TestClient


def _get_routes(app: FastAPI) -> list[tuple[str, str, str]]:
    """Return (path, method, route_id) for each API route."""
    routes: list[tuple[str, str, str]] = []
    for route in app.routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            for method in route.methods - {"HEAD", "OPTIONS"}:
                route_id = (
                    route.path.strip("/")
                    .replace("/", "_")
                    .replace("{", "")
                    .replace("}", "")
                    or "root"
                )
                routes.append((route.path, method, f"{route_id}_{method}"))
    return routes


def _fill_path_params(path: str) -> str:
    """Replace path params with sample values."""
    return re.sub(r"\{\w+\}", "1", path)


def _sample_request(
    client: TestClient, path: str, method: str
) -> dict[str, object] | list[object] | object | None:
    """Make a minimal request to the endpoint and return the JSON response."""
    url = _fill_path_params(path)
    if method == "GET":
        r = client.get(url)
    elif method == "POST":
        r = client.post(url, json={})
    elif method == "PUT":
        r = client.put(url, json={})
    elif method == "PATCH":
        r = client.patch(url, json={})
    elif method == "DELETE":
        r = client.delete(url)
    else:
        return None
    if r.status_code in (200, 201):
        try:
            return cast(
                dict[str, object] | list[object] | object,
                r.json(),
            )
        except Exception:
            return None
    if r.status_code == 204:
        return None
    return None


def export_openapi(app: FastAPI, include_examples: bool = False) -> dict[str, Any]:
    """
    Export OpenAPI schema for the FastAPI app.

    If include_examples is True, calls each endpoint with minimal input and
    populates response examples from the returned JSON.
    """
    schema = cast(dict[str, Any], app.openapi())
    if not include_examples:
        return schema

    with TestClient(app) as client:
        for path, methods in schema.get("paths", {}).items():
            for method in ("get", "post", "put", "patch", "delete"):
                op = methods.get(method)
                if op is None:
                    continue
                sample = _sample_request(client, path, method.upper())
                if "responses" not in op:
                    op["responses"] = {}
                if sample is not None:
                    if "200" not in op["responses"] and "201" not in op["responses"]:
                        op["responses"]["200"] = {"description": "Successful response"}
                    for code in ("200", "201"):
                        if code in op["responses"]:
                            content = op["responses"][code].setdefault("content", {})
                            json_content = content.setdefault("application/json", {})
                            json_content["example"] = sample
                            break
                elif method.upper() == "DELETE":
                    if "204" not in op["responses"]:
                        op["responses"]["204"] = {"description": "No Content"}
    return schema


def export_fixtures(app: FastAPI, output_path: str | Path) -> None:
    """
    Export JSON fixtures per endpoint to output_path.

    Calls each GET/POST endpoint with minimal input and saves the response
    to output_path/{route_id}_{METHOD}.json. Also writes openapi.json.
    """
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    schema = cast(dict[str, Any], app.openapi())
    with TestClient(app) as client:
        for path, methods in schema.get("paths", {}).items():
            for method in ("get", "post", "put", "patch", "delete"):
                op = methods.get(method)
                if op is None:
                    continue
                sample = _sample_request(client, path, method.upper())
                route_id = (
                    path.strip("/")
                    .replace("/", "_")
                    .replace("{", "")
                    .replace("}", "")
                    or "root"
                )
                filename = f"{route_id}_{method.upper()}.json"
                if sample is not None:
                    (output_dir / filename).write_text(
                        json.dumps(sample, indent=2)
                    )
                elif method.upper() == "DELETE":
                    (output_dir / filename).write_text(
                        json.dumps({"status": 204}, indent=2)
                    )

    (output_dir / "openapi.json").write_text(json.dumps(schema, indent=2))
