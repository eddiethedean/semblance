"""Process-local Databricks workspace graph and virtual clock."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from semblance_databricks.ids import make_id


@dataclass
class ClusterRecord:
    cluster_id: str
    cluster_name: str
    spark_version: str
    node_type_id: str
    state: str
    state_message: str = ""
    num_workers: int = 1
    ticks_remaining: int = 0
    fail_after: bool = False
    libraries: list[dict[str, Any]] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)
    deleted: bool = False


@dataclass
class JobRecord:
    job_id: str
    settings: dict[str, Any]
    created_time: int = 1_700_000_000_000
    creator_user_name: str = "user@acme.example"


@dataclass
class RunRecord:
    run_id: str
    job_id: str | None
    run_name: str
    life_cycle_state: str
    result_state: str | None = None
    ticks_remaining: int = 0
    output: dict[str, Any] = field(default_factory=dict)
    canceling: bool = False


@dataclass
class WarehouseRecord:
    id: str
    name: str
    state: str = "RUNNING"
    cluster_size: str = "X-Small"


@dataclass
class SecretScope:
    name: str
    keys: dict[str, str] = field(default_factory=dict)


@dataclass
class DbfsNode:
    path: str
    is_dir: bool
    data: bytes = b""


@dataclass
class WorkspaceObject:
    path: str
    object_type: str = "NOTEBOOK"
    language: str = "PYTHON"


class DatabricksState:
    def __init__(self, seed: int | None = 42) -> None:
        self.seed = seed
        self.revision = 0
        self.seq = 0
        self.clusters: dict[str, ClusterRecord] = {}
        self.jobs: dict[str, JobRecord] = {}
        self.runs: dict[str, RunRecord] = {}
        self.warehouses: dict[str, WarehouseRecord] = {}
        self.secret_scopes: dict[str, SecretScope] = {}
        self.dbfs: dict[str, DbfsNode] = {}
        self.workspace_objects: dict[str, WorkspaceObject] = {}
        self.permissions: dict[tuple[str, str], dict[str, Any]] = {}
        self.statements: dict[str, dict[str, Any]] = {}
        self.statement_callbacks: dict[str, Callable[..., Any]] = {}
        self.user = {
            "id": "1001",
            "userName": "user@acme.example",
            "displayName": "Acme User",
            "active": True,
        }

    def bump(self) -> None:
        self.revision += 1

    def next_seq(self) -> int:
        self.seq += 1
        return self.seq

    def allocate_numeric_id(self, existing: dict[str, Any], floor: int) -> str:
        used = {int(key) for key in existing if str(key).isdigit()}
        n = max([floor - 1, *used]) + 1
        while str(n) in existing:
            n += 1
        self.seq = max(self.seq, n)
        return str(n)

    def reindex_seq(self) -> None:
        nums = [int(k) for k in self.jobs if str(k).isdigit()]
        nums.extend(int(k) for k in self.runs if str(k).isdigit())
        if nums:
            self.seq = max(self.seq, max(nums))

    def clear(self) -> None:
        self.clusters.clear()
        self.jobs.clear()
        self.runs.clear()
        self.warehouses.clear()
        self.secret_scopes.clear()
        self.dbfs.clear()
        self.workspace_objects.clear()
        self.permissions.clear()
        self.statements.clear()
        self.revision = 0
        self.seq = 0

    def tick(self) -> None:
        for cluster in self.clusters.values():
            if cluster.deleted:
                continue
            if cluster.state in {"PENDING", "RESTARTING"}:
                if cluster.ticks_remaining > 0:
                    cluster.ticks_remaining -= 1
                if cluster.ticks_remaining <= 0:
                    if cluster.state == "RESTARTING":
                        cluster.state = "PENDING"
                        cluster.ticks_remaining = 1
                        cluster.events.append(
                            {"type": "PENDING", "message": "Restarting"}
                        )
                    elif cluster.fail_after:
                        cluster.state = "ERROR"
                        cluster.state_message = "Fixture startup failure"
                        cluster.events.append(
                            {"type": "ERROR", "message": cluster.state_message}
                        )
                    else:
                        cluster.state = "RUNNING"
                        cluster.state_message = ""
                        cluster.events.append({"type": "RUNNING", "message": "Running"})
            elif cluster.state == "TERMINATING":
                cluster.state = "TERMINATED"
                cluster.events.append({"type": "TERMINATED", "message": "Terminated"})
        for run in self.runs.values():
            if run.canceling:
                if run.life_cycle_state == "TERMINATING":
                    run.life_cycle_state = "TERMINATED"
                    run.result_state = "CANCELED"
                    run.canceling = False
                else:
                    run.life_cycle_state = "TERMINATING"
                continue
            if (
                run.life_cycle_state in {"PENDING", "RUNNING"}
                and run.ticks_remaining > 0
            ):
                run.ticks_remaining -= 1
                if run.life_cycle_state == "PENDING":
                    run.life_cycle_state = "RUNNING"
                    run.ticks_remaining = max(run.ticks_remaining, 1)
                elif run.ticks_remaining <= 0:
                    run.life_cycle_state = "TERMINATED"
                    run.result_state = run.result_state or "SUCCESS"

    def maybe_tick_real(self, clock: str) -> None:
        if clock == "real":
            self.tick()

    def add_cluster(
        self,
        cluster_name: str,
        *,
        cluster_id: str | None = None,
        spark_version: str = "13.3.x-scala2.12",
        node_type_id: str = "i3.xlarge",
        state: str = "RUNNING",
        ticks_remaining: int = 0,
        fail_after: bool = False,
        num_workers: int = 1,
    ) -> ClusterRecord:
        cid = cluster_id or make_id(
            "cluster", f"{cluster_name}:{self.next_seq()}", self.seed
        )
        if cid in self.clusters:
            raise ValueError(f"Duplicate cluster_id {cid}")
        rec = ClusterRecord(
            cluster_id=cid,
            cluster_name=cluster_name,
            spark_version=spark_version,
            node_type_id=node_type_id,
            state=state,
            ticks_remaining=ticks_remaining,
            fail_after=fail_after,
            num_workers=num_workers,
        )
        rec.events.append({"type": state, "message": f"Cluster {state}"})
        self.clusters[cid] = rec
        self.permissions[("clusters", cid)] = {
            "object_id": cid,
            "object_type": "clusters",
            "access_control_list": [],
        }
        self.bump()
        return rec

    def cluster_json(self, rec: ClusterRecord) -> dict[str, Any]:
        return {
            "cluster_id": rec.cluster_id,
            "cluster_name": rec.cluster_name,
            "spark_version": rec.spark_version,
            "node_type_id": rec.node_type_id,
            "state": rec.state,
            "state_message": rec.state_message,
            "num_workers": rec.num_workers,
            "libraries": rec.libraries,
        }

    def job_json(self, rec: JobRecord) -> dict[str, Any]:
        return {
            "job_id": int(rec.job_id) if rec.job_id.isdigit() else rec.job_id,
            "created_time": rec.created_time,
            "creator_user_name": rec.creator_user_name,
            "settings": rec.settings,
        }

    def run_json(self, rec: RunRecord) -> dict[str, Any]:
        state: dict[str, Any] = {"life_cycle_state": rec.life_cycle_state}
        if rec.result_state:
            state["result_state"] = rec.result_state
        body: dict[str, Any] = {
            "run_id": int(rec.run_id) if rec.run_id.isdigit() else rec.run_id,
            "run_name": rec.run_name,
            "state": state,
        }
        if rec.job_id:
            body["job_id"] = int(rec.job_id) if rec.job_id.isdigit() else rec.job_id
        return body
