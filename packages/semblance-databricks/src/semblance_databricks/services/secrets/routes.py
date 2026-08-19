"""Workspace secrets metadata (values never returned)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from semblance_databricks.errors import DatabricksError
from semblance_databricks.services.deps import mock_from
from semblance_databricks.state import SecretScope


async def _json_body(request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        return {}
    if not isinstance(body, dict):
        raise DatabricksError(400, "INVALID_PARAMETER_VALUE", "JSON object required")
    return body


def create_secrets_router() -> APIRouter:
    router = APIRouter()

    @router.get("/api/2.0/secrets/scopes/list")
    def list_scopes(request: Request) -> dict[str, Any]:
        mock = mock_from(request)
        return {"scopes": [{"name": s.name} for s in mock.state.secret_scopes.values()]}

    @router.get("/api/2.0/secrets/list")
    def list_secrets(request: Request, scope: str | None = None) -> dict[str, Any]:
        mock = mock_from(request)
        if not scope:
            raise DatabricksError(400, "INVALID_PARAMETER_VALUE", "scope required")
        rec = mock.state.secret_scopes.get(scope)
        if rec is None:
            raise DatabricksError(404, "RESOURCE_DOES_NOT_EXIST", "Scope not found")
        return {
            "secrets": [
                {"key": key, "last_updated_timestamp": 1_700_000_000_000}
                for key in rec.keys
            ]
        }

    @router.post("/api/2.0/secrets/put")
    async def put_secret(request: Request) -> dict[str, Any]:
        mock = mock_from(request)
        body = await _json_body(request)
        scope = str(body.get("scope", ""))
        key = str(body.get("key", ""))
        if not scope or not key:
            raise DatabricksError(
                400, "INVALID_PARAMETER_VALUE", "scope and key required"
            )
        rec = mock.state.secret_scopes.setdefault(scope, SecretScope(name=scope))
        rec.keys[key] = str(body.get("string_value", ""))
        mock.state.bump()
        return {}

    return router
