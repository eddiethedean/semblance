"""Permissions GET/PATCH."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from semblance_databricks.errors import DatabricksError
from semblance_databricks.services.deps import mock_from


def _key(object_type: str, object_id: str) -> tuple[str, str]:
    return (object_type, object_id)


def create_permissions_router() -> APIRouter:
    router = APIRouter()

    @router.get("/api/2.0/permissions/{object_type}/{object_id}")
    def get_permissions(
        request: Request, object_type: str, object_id: str
    ) -> dict[str, Any]:
        mock = mock_from(request)
        rec = mock.state.permissions.get(_key(object_type, object_id))
        if rec is None:
            raise DatabricksError(
                404, "RESOURCE_DOES_NOT_EXIST", "Permissions not found"
            )
        return rec

    @router.patch("/api/2.0/permissions/{object_type}/{object_id}")
    async def patch_permissions(
        request: Request, object_type: str, object_id: str
    ) -> dict[str, Any]:
        mock = mock_from(request)
        rec = mock.state.permissions.get(_key(object_type, object_id))
        if rec is None:
            raise DatabricksError(
                404, "RESOURCE_DOES_NOT_EXIST", "Permissions not found"
            )
        try:
            body = await request.json()
        except Exception:
            body = {}
        if not isinstance(body, dict):
            raise DatabricksError(
                400, "INVALID_PARAMETER_VALUE", "JSON object required"
            )
        acl = body.get("access_control_list")
        if isinstance(acl, list):
            rec["access_control_list"] = acl
        mock.state.bump()
        return rec

    return router
