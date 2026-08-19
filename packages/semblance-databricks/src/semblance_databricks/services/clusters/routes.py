"""Clusters list/get/create/edit/delete/restart/events/libraries."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from semblance_databricks.errors import DatabricksError
from semblance_databricks.http import json_object, require_int
from semblance_databricks.pagination import paginate
from semblance_databricks.services.deps import (
    mock_from,
    require_fail_stage,
    stub_unimplemented,
)


def create_clusters_router() -> APIRouter:
    router = APIRouter()

    def _list(
        request: Request, page_size: int | None, page_token: str | None
    ) -> dict[str, Any]:
        mock = mock_from(request)
        mock.state.maybe_tick_real(mock.config.clock)
        items = [
            mock.state.cluster_json(c)
            for c in sorted(mock.state.clusters.values(), key=lambda r: r.cluster_id)
            if not c.deleted
        ]
        page, nxt = paginate(
            items,
            page_size=page_size,
            page_token=page_token,
            resource="clusters",
            codec=mock.page_token_codec,
            revision=mock.state.revision,
            default_page_size=mock.config.default_page_size,
            max_page_size=mock.config.max_page_size,
        )
        body: dict[str, Any] = {"clusters": page}
        if nxt:
            body["next_page_token"] = nxt
        return body

    def _get(request: Request, cluster_id: str | None) -> dict[str, Any]:
        mock = mock_from(request)
        mock.state.maybe_tick_real(mock.config.clock)
        if not cluster_id:
            raise DatabricksError(400, "INVALID_PARAMETER_VALUE", "cluster_id required")
        rec = mock.state.clusters.get(cluster_id)
        if rec is None or rec.deleted:
            raise DatabricksError(
                404, "RESOURCE_DOES_NOT_EXIST", f"Cluster {cluster_id} not found"
            )
        return mock.state.cluster_json(rec)

    @router.get("/api/2.1/clusters/list")
    def list_21(
        request: Request,
        page_size: int | None = None,
        page_token: str | None = None,
    ) -> dict[str, Any]:
        return _list(request, page_size, page_token)

    @router.get("/api/2.1/clusters/get")
    def get_21(request: Request, cluster_id: str | None = None) -> dict[str, Any]:
        return _get(request, cluster_id)

    @router.get("/api/2.0/clusters/get")
    def get_20(request: Request, cluster_id: str | None = None) -> dict[str, Any]:
        return _get(request, cluster_id)

    @router.get("/api/2.0/clusters/list")
    def list_20(
        request: Request,
        page_size: int | None = None,
        page_token: str | None = None,
    ) -> dict[str, Any]:
        return _list(request, page_size, page_token)

    @router.post("/api/2.1/clusters/create")
    @router.post("/api/2.0/clusters/create")
    async def create(request: Request) -> dict[str, Any]:
        require_fail_stage(request, "before_validate")
        mock = mock_from(request)
        body = await json_object(request)
        require_fail_stage(request, "before_write")
        rec = mock.state.add_cluster(
            str(body.get("cluster_name", "cluster")),
            spark_version=str(body.get("spark_version", "13.3.x-scala2.12")),
            node_type_id=str(body.get("node_type_id", "i3.xlarge")),
            state="PENDING",
            ticks_remaining=require_int(
                body.get("startup_delay_ticks"), 1, "startup_delay_ticks"
            ),
            fail_after=bool(body.get("startup_failure", False)),
            num_workers=require_int(body.get("num_workers"), 1, "num_workers"),
        )
        require_fail_stage(request, "after_write")
        return {"cluster_id": rec.cluster_id}

    @router.post("/api/2.1/clusters/edit")
    @router.post("/api/2.0/clusters/edit")
    async def edit(request: Request) -> dict[str, Any]:
        mock = mock_from(request)
        body = await json_object(request)
        cid = str(body.get("cluster_id", ""))
        rec = mock.state.clusters.get(cid)
        if rec is None or rec.deleted:
            raise DatabricksError(404, "RESOURCE_DOES_NOT_EXIST", "Cluster not found")
        if "cluster_name" in body:
            rec.cluster_name = str(body["cluster_name"])
        if "num_workers" in body:
            rec.num_workers = require_int(body["num_workers"], 1, "num_workers")
        mock.state.bump()
        return {}

    @router.post("/api/2.1/clusters/delete")
    @router.post("/api/2.0/clusters/delete")
    async def delete(request: Request) -> dict[str, Any]:
        mock = mock_from(request)
        body = await json_object(request)
        cid = str(body.get("cluster_id", ""))
        rec = mock.state.clusters.get(cid)
        if rec is None or rec.deleted:
            raise DatabricksError(404, "RESOURCE_DOES_NOT_EXIST", "Cluster not found")
        rec.state = "TERMINATING"
        mock.state.bump()
        return {}

    @router.post("/api/2.1/clusters/restart")
    @router.post("/api/2.0/clusters/restart")
    async def restart(request: Request) -> dict[str, Any]:
        mock = mock_from(request)
        body = await json_object(request)
        cid = str(body.get("cluster_id", ""))
        rec = mock.state.clusters.get(cid)
        if rec is None or rec.deleted:
            raise DatabricksError(404, "RESOURCE_DOES_NOT_EXIST", "Cluster not found")
        rec.state = "RESTARTING"
        rec.ticks_remaining = 1
        rec.fail_after = False
        mock.state.bump()
        return {}

    @router.post("/api/2.1/clusters/permanent-delete")
    @router.post("/api/2.0/clusters/permanent-delete")
    async def permanent_delete(request: Request) -> dict[str, Any]:
        stub_unimplemented(request, "clusters/permanent-delete")
        return {}

    @router.post("/api/2.1/clusters/events")
    @router.post("/api/2.0/clusters/events")
    async def events(request: Request) -> dict[str, Any]:
        mock = mock_from(request)
        body = await json_object(request)
        cid = str(body.get("cluster_id", ""))
        rec = mock.state.clusters.get(cid)
        if rec is None or rec.deleted:
            raise DatabricksError(404, "RESOURCE_DOES_NOT_EXIST", "Cluster not found")
        return {"events": rec.events, "total_count": len(rec.events)}

    @router.post("/api/2.0/libraries/install")
    async def install(request: Request) -> dict[str, Any]:
        mock = mock_from(request)
        body = await json_object(request)
        cid = str(body.get("cluster_id", ""))
        rec = mock.state.clusters.get(cid)
        if rec is None or rec.deleted:
            raise DatabricksError(404, "RESOURCE_DOES_NOT_EXIST", "Cluster not found")
        rec.libraries.extend(list(body.get("libraries") or []))
        return {}

    @router.post("/api/2.0/libraries/uninstall")
    async def uninstall(request: Request) -> dict[str, Any]:
        mock = mock_from(request)
        body = await json_object(request)
        cid = str(body.get("cluster_id", ""))
        rec = mock.state.clusters.get(cid)
        if rec is None or rec.deleted:
            raise DatabricksError(404, "RESOURCE_DOES_NOT_EXIST", "Cluster not found")
        requested = list(body.get("libraries") or [])
        if requested:
            rec.libraries = [lib for lib in rec.libraries if lib not in requested]
        else:
            rec.libraries = []
        return {}

    return router
