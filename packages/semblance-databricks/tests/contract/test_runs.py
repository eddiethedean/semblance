from fastapi.testclient import TestClient

from semblance_databricks import DatabricksMock, DatabricksMockConfig


def test_get_run(client: TestClient) -> None:
    r = client.get("/api/2.2/jobs/runs/get?run_id=2001")
    assert r.status_code == 200
    body = r.json()
    assert body["run_id"] == 2001
    assert body["state"]["life_cycle_state"] == "TERMINATED"
    assert body["state"]["result_state"] == "SUCCESS"


def test_get_output(client: TestClient) -> None:
    r = client.get("/api/2.2/jobs/runs/get-output?run_id=2001")
    assert r.status_code == 200
    assert r.json()["notebook_output"]["result"] == "ok"


def test_submit_and_cancel() -> None:
    mock = DatabricksMock(DatabricksMockConfig(seed=42, clock="virtual"))
    mock.load_bundled_fixture()
    client = TestClient(mock.as_fastapi())
    submitted = client.post("/api/2.2/jobs/runs/submit", json={"job_id": 1001})
    assert submitted.status_code == 200
    rid = submitted.json()["run_id"]
    pending = client.get(f"/api/2.2/jobs/runs/get?run_id={rid}")
    assert pending.json()["state"]["life_cycle_state"] == "PENDING"
    mock.tick()
    running = client.get(f"/api/2.2/jobs/runs/get?run_id={rid}")
    assert running.json()["state"]["life_cycle_state"] == "RUNNING"
    canceled = client.post("/api/2.2/jobs/runs/cancel", json={"run_id": rid})
    assert canceled.status_code == 200
    mock.tick()
    done = client.get(f"/api/2.2/jobs/runs/get?run_id={rid}")
    assert done.json()["state"]["life_cycle_state"] == "TERMINATED"
    assert done.json()["state"]["result_state"] == "CANCELED"
