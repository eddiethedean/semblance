"""Fixture v1 schema and loaders. YAML/JSON is data only — never evaluated."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

from semblance_databricks.state import (
    DatabricksState,
    DbfsNode,
    JobRecord,
    RunRecord,
    SecretScope,
    WarehouseRecord,
    WorkspaceObject,
)


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class FixtureWorkspace(_Strict):
    workspace_id: str = Field(alias="workspaceId", default="1234567890")
    name: str = "acme"


class FixtureCluster(_Strict):
    cluster_id: str | None = Field(default=None, alias="cluster_id")
    cluster_name: str
    spark_version: str = "13.3.x-scala2.12"
    node_type_id: str = "i3.xlarge"
    state: str = "RUNNING"
    num_workers: int = 1
    startup_delay_ticks: int = 0
    startup_failure: bool = False


class FixtureJob(_Strict):
    job_id: str | None = None
    name: str
    creator_user_name: str = "user@acme.example"


class FixtureRun(_Strict):
    run_id: str | None = None
    job_id: str | None = None
    run_name: str = "nightly"
    life_cycle_state: str = "TERMINATED"
    result_state: str | None = "SUCCESS"
    output_notebook: str | None = None


class FixtureWarehouse(_Strict):
    id: str | None = None
    name: str
    state: str = "RUNNING"


class FixtureSecretScope(_Strict):
    name: str
    keys: list[str] = Field(default_factory=list)


class FixtureDbfs(_Strict):
    path: str
    is_dir: bool = False
    content: str = ""


class FixtureWorkspaceObject(_Strict):
    path: str
    object_type: str = "NOTEBOOK"


class FixtureDocument(_Strict):
    version: int
    workspace: FixtureWorkspace = Field(default_factory=FixtureWorkspace)
    clusters: list[FixtureCluster] = Field(default_factory=list)
    jobs: list[FixtureJob] = Field(default_factory=list)
    runs: list[FixtureRun] = Field(default_factory=list)
    warehouses: list[FixtureWarehouse] = Field(default_factory=list)
    secret_scopes: list[FixtureSecretScope] = Field(
        default_factory=list, alias="secretScopes"
    )
    dbfs: list[FixtureDbfs] = Field(default_factory=list)
    workspace_objects: list[FixtureWorkspaceObject] = Field(
        default_factory=list, alias="workspaceObjects"
    )


def parse_fixture(data: dict[str, Any]) -> FixtureDocument:
    doc = FixtureDocument.model_validate(data)
    if doc.version != 1:
        raise ValueError("only fixture version 1 is supported")
    return doc


def load_fixture_file(path: str | Path) -> FixtureDocument:
    raw = Path(path).read_text(encoding="utf-8")
    if Path(path).suffix.lower() in {".yaml", ".yml"}:
        loaded = yaml.safe_load(raw)
    else:
        import json

        loaded = json.loads(raw)
    if not isinstance(loaded, dict):
        raise ValueError("fixture root must be a mapping")
    return parse_fixture(loaded)


def apply_fixture(doc: FixtureDocument, state: DatabricksState) -> None:
    seen_jobs: set[str] = set()
    for cluster in doc.clusters:
        rec = state.add_cluster(
            cluster.cluster_name,
            cluster_id=cluster.cluster_id,
            spark_version=cluster.spark_version,
            node_type_id=cluster.node_type_id,
            state=cluster.state,
            ticks_remaining=cluster.startup_delay_ticks,
            fail_after=cluster.startup_failure,
            num_workers=cluster.num_workers,
        )
        _ = rec
    for job in doc.jobs:
        jid = job.job_id or str(1000 + len(state.jobs) + 1)
        if jid in seen_jobs or jid in state.jobs:
            raise ValueError(f"Duplicate job_id {jid}")
        seen_jobs.add(jid)
        state.jobs[jid] = JobRecord(
            job_id=jid,
            settings={"name": job.name},
            creator_user_name=job.creator_user_name,
        )
        state.permissions[("jobs", jid)] = {
            "object_id": jid,
            "object_type": "job",
            "access_control_list": [
                {
                    "user_name": job.creator_user_name,
                    "all_permissions": [{"permission_level": "CAN_MANAGE"}],
                }
            ],
        }
    for run in doc.runs:
        rid = run.run_id or str(2000 + len(state.runs) + 1)
        if rid in state.runs:
            raise ValueError(f"Duplicate run_id {rid}")
        if run.job_id and run.job_id not in state.jobs:
            raise ValueError(f"Dangling job_id {run.job_id} on run")
        state.runs[rid] = RunRecord(
            run_id=rid,
            job_id=run.job_id,
            run_name=run.run_name,
            life_cycle_state=run.life_cycle_state,
            result_state=run.result_state,
            output={"notebook_output": {"result": run.output_notebook or "ok"}},
        )
    for wh in doc.warehouses:
        wid = wh.id or f"wh-{len(state.warehouses) + 1}"
        if wid in state.warehouses:
            raise ValueError(f"Duplicate warehouse id {wid}")
        state.warehouses[wid] = WarehouseRecord(id=wid, name=wh.name, state=wh.state)
    for scope in doc.secret_scopes:
        if scope.name in state.secret_scopes:
            raise ValueError(f"Duplicate secret scope {scope.name}")
        state.secret_scopes[scope.name] = SecretScope(
            name=scope.name,
            keys={k: "redacted" for k in scope.keys},
        )
    for node in doc.dbfs:
        state.dbfs[node.path] = DbfsNode(
            path=node.path,
            is_dir=node.is_dir,
            data=node.content.encode(),
        )
    for obj in doc.workspace_objects:
        state.workspace_objects[obj.path] = WorkspaceObject(
            path=obj.path, object_type=obj.object_type
        )
    state.bump()


def bundled_acme_path() -> Path:
    return Path(__file__).resolve().parent / "defaults" / "acme.yaml"


def load_bundled_fixture(name: str = "acme") -> FixtureDocument:
    if name != "acme":
        raise ValueError(f"unknown bundled fixture {name!r}; expected 'acme'")
    return load_fixture_file(bundled_acme_path())
