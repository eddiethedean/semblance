"""DBFS list/read, put, and add-block stub."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request

from semblance_databricks.errors import DatabricksError
from semblance_databricks.http import json_object
from semblance_databricks.services.deps import mock_from, stub_unimplemented
from semblance_databricks.state import DbfsNode


def _normalize(path: str) -> str:
    raw = path.replace("\\", "/")
    if not raw.startswith("/"):
        raw = "/" + raw
    parts: list[str] = []
    for seg in raw.split("/"):
        if seg in {"", "."}:
            continue
        if seg == ".." or ":" in seg:
            raise DatabricksError(400, "INVALID_PARAMETER_VALUE", "Invalid path")
        parts.append(seg)
    return "/" + "/".join(parts) if parts else "/"


def _parent(path: str) -> str:
    if path in {"", "/"}:
        return "/"
    stripped = path.rstrip("/")
    idx = stripped.rfind("/")
    return stripped[:idx] or "/"


def _write_temp(root: str, dbfs_path: str, data: bytes) -> None:
    base = Path(root).resolve()
    rel = dbfs_path.lstrip("/")
    dest = base.joinpath(*rel.split("/")).resolve()
    try:
        dest.relative_to(base)
    except ValueError as exc:
        raise DatabricksError(400, "INVALID_PARAMETER_VALUE", "Invalid path") from exc
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)


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
        if offset < 0 or length < 0:
            raise DatabricksError(
                400, "INVALID_PARAMETER_VALUE", "offset and length must be >= 0"
            )
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
        body = await json_object(request)
        path = _normalize(str(body.get("path", "")))
        if not path or path == "/":
            raise DatabricksError(400, "INVALID_PARAMETER_VALUE", "path required")
        replacing = path in mock.state.dbfs
        if not replacing and len(mock.state.dbfs) >= mock.config.dbfs_max_files:
            raise DatabricksError(400, "MAX_BLOCK_SIZE_EXCEEDED", "DBFS file cap")
        raw = str(body.get("contents", ""))
        try:
            content = base64.b64decode(raw, validate=True)
        except Exception as exc:
            raise DatabricksError(
                400, "INVALID_PARAMETER_VALUE", "contents must be base64"
            ) from exc
        existing = mock.state.dbfs.get(path)
        old_size = len(existing.data) if existing is not None else 0
        total = (
            sum(len(n.data) for n in mock.state.dbfs.values()) - old_size + len(content)
        )
        if total > mock.config.dbfs_max_bytes:
            raise DatabricksError(400, "MAX_BLOCK_SIZE_EXCEEDED", "DBFS size cap")
        mock.state.dbfs[path] = DbfsNode(path=path, is_dir=False, data=content)
        if mock.config.dbfs_temp_dir:
            _write_temp(mock.config.dbfs_temp_dir, path, content)
        mock.state.bump()
        return {}

    return router
