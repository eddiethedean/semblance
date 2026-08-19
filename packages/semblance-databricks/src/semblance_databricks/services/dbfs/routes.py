"""DBFS list/read and add-block stub."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request

from semblance_databricks.errors import DatabricksError
from semblance_databricks.services.deps import mock_from, stub_unimplemented
from semblance_databricks.state import DbfsNode


def _normalize(path: str) -> str:
    if not path.startswith("/"):
        path = "/" + path
    return path.rstrip("/") or "/"


def _parent(path: str) -> str:
    if path in {"", "/"}:
        return "/"
    stripped = path.rstrip("/")
    idx = stripped.rfind("/")
    return stripped[:idx] or "/"


def create_dbfs_router() -> APIRouter:
    router = APIRouter()

    @router.get("/api/2.0/dbfs/list")
    def list_dbfs(request: Request, path: str | None = None) -> dict[str, Any]:
        mock = mock_from(request)
        if not path:
            raise DatabricksError(400, "INVALID_PARAMETER_VALUE", "path required")
        prefix = _normalize(path)
        files: list[dict[str, Any]] = []
        for node in mock.state.dbfs.values():
            parent = _parent(node.path)
            if parent == prefix:
                if node.path == prefix:
                    continue
                files.append(
                    {
                        "path": node.path,
                        "is_dir": node.is_dir,
                        "file_size": 0 if node.is_dir else len(node.data),
                    }
                )
        if prefix not in mock.state.dbfs and not files:
            raise DatabricksError(404, "RESOURCE_DOES_NOT_EXIST", "Path not found")
        return {"files": files}

    @router.get("/api/2.0/dbfs/read")
    def read_dbfs(
        request: Request,
        path: str | None = None,
        offset: int = 0,
        length: int = 1048576,
    ) -> dict[str, Any]:
        mock = mock_from(request)
        if not path:
            raise DatabricksError(400, "INVALID_PARAMETER_VALUE", "path required")
        node = mock.state.dbfs.get(_normalize(path))
        if node is None or node.is_dir:
            raise DatabricksError(404, "RESOURCE_DOES_NOT_EXIST", "File not found")
        data = node.data[offset : offset + length]
        return {
            "bytes_read": len(data),
            "data": base64.b64encode(data).decode(),
        }

    @router.post("/api/2.0/dbfs/add-block")
    async def add_block(request: Request) -> dict[str, Any]:
        stub_unimplemented(request, "dbfs/add-block")
        return {}

    @router.post("/api/2.0/dbfs/put")
    async def put_file(request: Request) -> dict[str, Any]:
        mock = mock_from(request)
        try:
            body = await request.json()
        except Exception:
            body = {}
        if not isinstance(body, dict):
            raise DatabricksError(
                400, "INVALID_PARAMETER_VALUE", "JSON object required"
            )
        path = _normalize(str(body.get("path", "")))
        if not path or path == "/":
            raise DatabricksError(400, "INVALID_PARAMETER_VALUE", "path required")
        if len(mock.state.dbfs) >= mock.config.dbfs_max_files:
            raise DatabricksError(400, "MAX_BLOCK_SIZE_EXCEEDED", "DBFS file cap")
        content = str(body.get("contents", "")).encode()
        total = sum(len(n.data) for n in mock.state.dbfs.values()) + len(content)
        if total > mock.config.dbfs_max_bytes:
            raise DatabricksError(400, "MAX_BLOCK_SIZE_EXCEEDED", "DBFS size cap")
        mock.state.dbfs[path] = DbfsNode(path=path, is_dir=False, data=content)
        if mock.config.dbfs_temp_dir:
            dest = Path(mock.config.dbfs_temp_dir) / path.lstrip("/")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(content)
        mock.state.bump()
        return {}

    return router
