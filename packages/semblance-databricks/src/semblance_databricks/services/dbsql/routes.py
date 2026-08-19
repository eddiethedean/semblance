"""SQL warehouses and statement execution (no Spark)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from semblance_databricks.errors import DatabricksError
from semblance_databricks.http import json_object
from semblance_databricks.ids import make_id
from semblance_databricks.pagination import paginate
from semblance_databricks.services.deps import mock_from
from semblance_databricks.state import WarehouseRecord


def _statement_payload(statement_id: str, rec: dict[str, Any]) -> dict[str, Any]:
    chunks: list[Any] = rec.get("chunks") or []
    index = int(rec.get("chunk_index", 0))
    chunk = chunks[index] if index < len(chunks) else []
    next_chunk = None
    if index + 1 < len(chunks):
        next_chunk = index + 1
    result: dict[str, Any] = {
        "chunk_index": index,
        "row_count": len(chunk) if isinstance(chunk, list) else 0,
        "data_array": chunk,
    }
    if next_chunk is not None:
        result["next_chunk_internal"] = next_chunk
    return {
        "statement_id": statement_id,
        "status": {"state": rec.get("state", "SUCCEEDED")},
        "manifest": {
            "format": "JSON_ARRAY",
            "total_chunk_count": len(chunks),
            "total_row_count": sum(
                len(c) if isinstance(c, list) else 0 for c in chunks
            ),
        },
        "result": result,
    }


def create_dbsql_router() -> APIRouter:
    router = APIRouter()

    @router.get("/api/2.0/sql/warehouses")
    def list_warehouses(
        request: Request,
        page_size: int | None = None,
        page_token: str | None = None,
    ) -> dict[str, Any]:
        mock = mock_from(request)
        items = [
            {
                "id": w.id,
                "name": w.name,
                "state": w.state,
                "cluster_size": w.cluster_size,
            }
            for w in mock.state.warehouses.values()
        ]
        page, nxt = paginate(
            items,
            page_size=page_size,
            page_token=page_token,
            resource="warehouses",
            codec=mock.page_token_codec,
            revision=mock.state.revision,
            default_page_size=mock.config.default_page_size,
            max_page_size=mock.config.max_page_size,
        )
        body: dict[str, Any] = {"warehouses": page}
        if nxt:
            body["next_page_token"] = nxt
        return body

    @router.post("/api/2.0/sql/warehouses")
    async def create_warehouse(request: Request) -> dict[str, Any]:
        mock = mock_from(request)
        body = await json_object(request)
        name = str(body.get("name", "warehouse"))
        wid = make_id("warehouse", f"{name}:{mock.state.next_seq()}", mock.config.seed)
        rec = WarehouseRecord(
            id=wid,
            name=name,
            cluster_size=str(body.get("cluster_size", "X-Small")),
        )
        mock.state.warehouses[wid] = rec
        mock.state.permissions[("warehouses", wid)] = {
            "object_id": wid,
            "object_type": "warehouses",
            "access_control_list": [],
        }
        mock.state.bump()
        return {"id": wid}

    @router.get("/api/2.0/sql/warehouses/{warehouse_id}")
    def get_warehouse(request: Request, warehouse_id: str) -> dict[str, Any]:
        mock = mock_from(request)
        rec = mock.state.warehouses.get(warehouse_id)
        if rec is None:
            raise DatabricksError(404, "RESOURCE_DOES_NOT_EXIST", "Warehouse not found")
        return {
            "id": rec.id,
            "name": rec.name,
            "state": rec.state,
            "cluster_size": rec.cluster_size,
        }

    @router.delete("/api/2.0/sql/warehouses/{warehouse_id}")
    def delete_warehouse(request: Request, warehouse_id: str) -> dict[str, Any]:
        mock = mock_from(request)
        if warehouse_id not in mock.state.warehouses:
            raise DatabricksError(404, "RESOURCE_DOES_NOT_EXIST", "Warehouse not found")
        del mock.state.warehouses[warehouse_id]
        mock.state.bump()
        return {}

    @router.post("/api/2.0/sql/statements")
    async def execute_statement(request: Request) -> dict[str, Any]:
        mock = mock_from(request)
        body = await json_object(request)
        warehouse_id = str(body.get("warehouse_id") or "")
        sql = str(body.get("statement", ""))
        if not warehouse_id:
            raise DatabricksError(
                400, "INVALID_PARAMETER_VALUE", "warehouse_id required"
            )
        if warehouse_id not in mock.state.warehouses:
            raise DatabricksError(404, "RESOURCE_DOES_NOT_EXIST", "Warehouse not found")
        sid = make_id("statement", f"{sql}:{mock.state.next_seq()}", mock.config.seed)
        callback = mock.state.statement_callbacks.get(
            sql
        ) or mock.state.statement_callbacks.get(warehouse_id)
        if callback is not None:
            payload = callback(body, mock.state)
            chunks = payload.get("chunks", payload.get("data_array", [["1"]]))
            if chunks and not isinstance(chunks[0], list):
                chunks = [chunks]
        else:
            chunks = [[["ok"]]]
        rec = {"state": "SUCCEEDED", "chunks": chunks, "chunk_index": 0}
        mock.state.statements[sid] = rec
        mock.state.bump()
        return _statement_payload(sid, rec)

    @router.get("/api/2.0/sql/statements/{statement_id}")
    def get_statement(
        request: Request,
        statement_id: str,
        chunk_index: int | None = None,
    ) -> dict[str, Any]:
        mock = mock_from(request)
        rec = mock.state.statements.get(statement_id)
        if rec is None:
            raise DatabricksError(404, "RESOURCE_DOES_NOT_EXIST", "Statement not found")
        if chunk_index is not None:
            rec = {**rec, "chunk_index": chunk_index}
        return _statement_payload(statement_id, rec)

    return router
