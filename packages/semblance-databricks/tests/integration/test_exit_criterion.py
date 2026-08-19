from fastapi.testclient import TestClient

from semblance_databricks.testing import DatabricksMockContext


def test_exit_criterion_http_flow(mock, client: TestClient) -> None:
    first = client.get("/api/2.1/clusters/list?page_size=2")
    assert first.status_code == 200
    token = first.json()["next_page_token"]
    second = client.get(f"/api/2.1/clusters/list?page_size=2&page_token={token}")
    assert second.status_code == 200
    assert len(first.json()["clusters"]) == 2
    assert len(second.json()["clusters"]) == 2

    cluster = client.get("/api/2.1/clusters/get?cluster_id=0101-acme-0001")
    assert cluster.status_code == 200

    job = client.get("/api/2.2/jobs/get?job_id=1001")
    assert job.status_code == 200

    run = client.get("/api/2.2/jobs/runs/get?run_id=2001")
    assert run.status_code == 200

    created = client.post(
        "/api/2.1/clusters/create",
        json={"cluster_name": "exit", "startup_delay_ticks": 1},
    )
    cid = created.json()["cluster_id"]
    assert client.get(f"/api/2.1/clusters/get?cluster_id={cid}").json()["state"] == (
        "PENDING"
    )
    mock.tick()
    assert client.get(f"/api/2.1/clusters/get?cluster_id={cid}").json()["state"] == (
        "RUNNING"
    )

    secrets = client.get("/api/2.0/secrets/list", params={"scope": "acme-scope"})
    assert secrets.status_code == 200
    assert "value" not in secrets.json()["secrets"][0]
    assert "redacted" not in secrets.text

    status = client.get(
        "/api/2.0/workspace/get-status",
        params={"path": "/Users/user@acme.example/notebook"},
    )
    assert status.status_code == 200

    perms = client.get("/api/2.0/permissions/jobs/1001")
    assert perms.status_code == 200

    sql = client.post(
        "/api/2.0/sql/statements",
        json={"warehouse_id": "wh-acme", "statement": "SELECT 1"},
    )
    assert sql.status_code == 200

    events = client.post(
        "/api/2.1/clusters/events", json={"cluster_id": "0101-acme-0001"}
    )
    assert events.status_code == 200

    dbfs = client.get("/api/2.0/dbfs/list", params={"path": "/mnt/acme"})
    assert dbfs.status_code == 200


def test_context_resets_state() -> None:
    with DatabricksMockContext(seed=42) as client:
        client.get("/api/2.1/clusters/list")
    with DatabricksMockContext(seed=42) as client:
        r = client.get("/api/2.1/clusters/list")
        assert r.status_code == 200
        assert len(r.json()["clusters"]) == 4
