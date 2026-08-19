"""Workspace get-status and current user."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from semblance_databricks.errors import DatabricksError
from semblance_databricks.services.deps import mock_from


def create_workspace_router() -> APIRouter:
    router = APIRouter()

    @router.get("/api/2.0/workspace/get-status")
    def get_status(request: Request, path: str | None = None) -> dict[str, Any]:
        mock = mock_from(request)
        if not path:
            raise DatabricksError(400, "INVALID_PARAMETER_VALUE", "path required")
        obj = mock.state.workspace_objects.get(path)
        if obj is None:
            raise DatabricksError(
                404,
                "RESOURCE_DOES_NOT_EXIST",
                f"Path {path} does not exist",
            )
        return {
            "path": obj.path,
            "object_type": obj.object_type,
            "language": obj.language,
        }

    @router.get("/api/2.0/preview/scim/v2/Me")
    def me(request: Request) -> dict[str, Any]:
        mock = mock_from(request)
        return dict(mock.state.user)

    return router
