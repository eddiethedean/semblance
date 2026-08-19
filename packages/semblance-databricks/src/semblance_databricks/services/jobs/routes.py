"""Jobs 2.2 (primary) and 2.1 representative aliases."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from semblance_databricks.errors import DatabricksError
from semblance_databricks.pagination import paginate
from semblance_databricks.services.deps import mock_from, require_fail_stage
from semblance_databricks.state import JobRecord, RunRecord


async def _json_body(request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        return {}
    if not isinstance(body, dict):
        raise DatabricksError(400, "INVALID_PARAMETER_VALUE", "JSON object required")
    return body


def _add_jobs_routes(router: APIRouter, prefix: str) -> None:
    slug = prefix.replace("/", "_")

    @router.get(f"{prefix}/jobs/list", name=f"list_jobs{slug}")
    def list_jobs(
        request: Request,
        limit: int | None = None,
        page_token: str | None = None,
    ) -> dict[str, Any]:
        mock = mock_from(request)
        jobs = sorted(mock.state.jobs.values(), key=lambda rec: rec.job_id)
        items = [mock.state.job_json(job) for job in jobs]
        page, nxt = paginate(
            items,
            page_size=limit,
            page_token=page_token,
            resource="jobs",
            codec=mock.page_token_codec,
            revision=mock.state.revision,
            default_page_size=mock.config.default_page_size,
            max_page_size=mock.config.max_page_size,
        )
        body: dict[str, Any] = {"jobs": page, "has_more": nxt is not None}
        if nxt:
            body["next_page_token"] = nxt
        return body

    @router.get(f"{prefix}/jobs/get", name=f"get_job{slug}")
    def get_job(request: Request, job_id: str | None = None) -> dict[str, Any]:
        mock = mock_from(request)
        if not job_id:
            raise DatabricksError(400, "INVALID_PARAMETER_VALUE", "job_id required")
        rec = mock.state.jobs.get(str(job_id))
        if rec is None:
            raise DatabricksError(404, "RESOURCE_DOES_NOT_EXIST", "Job not found")
        return mock.state.job_json(rec)

    @router.get(f"{prefix}/jobs/runs/get", name=f"get_run{slug}")
    def get_run(request: Request, run_id: str | None = None) -> dict[str, Any]:
        mock = mock_from(request)
        mock.state.maybe_tick_real(mock.config.clock)
        if not run_id:
            raise DatabricksError(400, "INVALID_PARAMETER_VALUE", "run_id required")
        rec = mock.state.runs.get(str(run_id))
        if rec is None:
            raise DatabricksError(404, "RESOURCE_DOES_NOT_EXIST", "Run not found")
        return mock.state.run_json(rec)

    @router.post(f"{prefix}/jobs/create", name=f"create_job{slug}")
    async def create_job(request: Request) -> dict[str, Any]:
        require_fail_stage(request, "before_write")
        mock = mock_from(request)
        body = await _json_body(request)
        jid = str(1000 + mock.state.next_seq())
        settings_raw = body.get("settings")
        settings: dict[str, Any] = (
            dict(settings_raw) if isinstance(settings_raw, dict) else {}
        )
        name = str(body.get("name") or settings.get("name") or "job")
        merged = {"name": name, **settings}
        mock.state.jobs[jid] = JobRecord(job_id=jid, settings=merged)
        mock.state.permissions[("jobs", jid)] = {
            "object_id": jid,
            "object_type": "job",
            "access_control_list": [],
        }
        mock.state.bump()
        return {"job_id": int(jid)}

    @router.post(f"{prefix}/jobs/reset", name=f"reset_job{slug}")
    async def reset_job(request: Request) -> dict[str, Any]:
        mock = mock_from(request)
        body = await _json_body(request)
        jid = str(body.get("job_id", ""))
        rec = mock.state.jobs.get(jid)
        if rec is None:
            raise DatabricksError(404, "RESOURCE_DOES_NOT_EXIST", "Job not found")
        settings = body.get("new_settings") or body.get("settings") or {}
        rec.settings = dict(settings)
        mock.state.bump()
        return {}

    @router.post(f"{prefix}/jobs/delete", name=f"delete_job{slug}")
    async def delete_job(request: Request) -> dict[str, Any]:
        mock = mock_from(request)
        body = await _json_body(request)
        jid = str(body.get("job_id", ""))
        if jid not in mock.state.jobs:
            raise DatabricksError(404, "RESOURCE_DOES_NOT_EXIST", "Job not found")
        del mock.state.jobs[jid]
        mock.state.bump()
        return {}

    @router.post(f"{prefix}/jobs/runs/submit", name=f"submit_run{slug}")
    async def submit_run(request: Request) -> dict[str, Any]:
        mock = mock_from(request)
        body = await _json_body(request)
        rid = str(2000 + mock.state.next_seq())
        job_id = str(body["job_id"]) if body.get("job_id") is not None else None
        mock.state.runs[rid] = RunRecord(
            run_id=rid,
            job_id=job_id,
            run_name=str(body.get("run_name", "submit")),
            life_cycle_state="PENDING",
            ticks_remaining=2,
            output={"notebook_output": {"result": "pending"}},
        )
        mock.state.bump()
        return {"run_id": int(rid)}

    @router.post(f"{prefix}/jobs/runs/cancel", name=f"cancel_run{slug}")
    async def cancel_run(request: Request) -> dict[str, Any]:
        mock = mock_from(request)
        body = await _json_body(request)
        rid = str(body.get("run_id", ""))
        rec = mock.state.runs.get(rid)
        if rec is None:
            raise DatabricksError(404, "RESOURCE_DOES_NOT_EXIST", "Run not found")
        rec.canceling = True
        rec.life_cycle_state = "TERMINATING"
        mock.state.bump()
        return {}

    @router.get(f"{prefix}/jobs/runs/get-output", name=f"get_output{slug}")
    def get_output(request: Request, run_id: str | None = None) -> dict[str, Any]:
        mock = mock_from(request)
        if not run_id:
            raise DatabricksError(400, "INVALID_PARAMETER_VALUE", "run_id required")
        rec = mock.state.runs.get(str(run_id))
        if rec is None:
            raise DatabricksError(404, "RESOURCE_DOES_NOT_EXIST", "Run not found")
        return {
            "metadata": mock.state.run_json(rec),
            "notebook_output": rec.output.get("notebook_output", {"result": ""}),
        }


def create_jobs_router() -> APIRouter:
    router = APIRouter()
    _add_jobs_routes(router, "/api/2.2")
    _add_jobs_routes(router, "/api/2.1")
    return router
