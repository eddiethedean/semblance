"""Shared request parsing for Databricks REST handlers."""

from __future__ import annotations

import json
from typing import Any

from fastapi import Request

from semblance_databricks.errors import DatabricksError


async def json_object(request: Request) -> dict[str, Any]:
    raw = await request.body()
    if not raw:
        return {}
    try:
        body = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise DatabricksError(400, "INVALID_PARAMETER_VALUE", "Invalid JSON") from exc
    if not isinstance(body, dict):
        raise DatabricksError(400, "INVALID_PARAMETER_VALUE", "JSON object required")
    return body


def require_int(value: Any, default: int, name: str) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise DatabricksError(
            400, "INVALID_PARAMETER_VALUE", f"{name} must be an integer"
        ) from exc
