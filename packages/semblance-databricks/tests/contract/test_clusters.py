from fastapi.testclient import TestClient

from semblance_databricks import DatabricksMock, DatabricksMockConfig


def test_list_clusters(client: TestClient) -> None:
    r = client.get("/api/2.1/clusters/list?page_size=2")
    assert r.status_code == 200
    body = r.json()
    assert len(body["clusters"]) == 2
    assert "next_page_token" in body
    first = body["clusters"][0]
    assert {
        "cluster_id",
        "cluster_name",
        "spark_version",
        "node_type_id",
        "state",
    } <= set(first)


def test_list_clusters_second_page(client: TestClient) -> None:
    first = client.get("/api/2.1/clusters/list?page_size=2")
    token = first.json()["next_page_token"]
    second = client.get(f"/api/2.1/clusters/list?page_size=2&page_token={token}")
    assert second.status_code == 200
    assert len(second.json()["clusters"]) == 2
    ids1 = {c["cluster_id"] for c in first.json()["clusters"]}
    ids2 = {c["cluster_id"] for c in second.json()["clusters"]}
    assert ids1.isdisjoint(ids2)


def test_get_cluster(client: TestClient) -> None:
    r = client.get("/api/2.1/clusters/get?cluster_id=0101-acme-0001")
    assert r.status_code == 200
    assert r.json()["cluster_name"] == "ingest-1"


def test_get_cluster_missing(client: TestClient) -> None:
    r = client.get("/api/2.1/clusters/get?cluster_id=missing")
    assert r.status_code == 404
    assert r.json()["error_code"] == "RESOURCE_DOES_NOT_EXIST"


def test_tampered_page_token(client: TestClient) -> None:
    r = client.get("/api/2.1/clusters/list?page_token=not-a-token")
    assert r.status_code == 400
    assert r.json()["error_code"] == "INVALID_PARAMETER_VALUE"


def test_create_cluster_virtual_clock() -> None:
    mock = DatabricksMock(DatabricksMockConfig(seed=42, clock="virtual"))
    mock.load_bundled_fixture()
    client = TestClient(mock.as_fastapi())
    created = client.post(
        "/api/2.1/clusters/create",
        json={"cluster_name": "new", "startup_delay_ticks": 1},
    )
    assert created.status_code == 200
    cid = created.json()["cluster_id"]
    pending = client.get(f"/api/2.1/clusters/get?cluster_id={cid}")
    assert pending.json()["state"] == "PENDING"
    mock.tick()
    running = client.get(f"/api/2.1/clusters/get?cluster_id={cid}")
    assert running.json()["state"] == "RUNNING"


def test_edit_cluster(client: TestClient) -> None:
    r = client.post(
        "/api/2.1/clusters/edit",
        json={"cluster_id": "0101-acme-0001", "cluster_name": "renamed"},
    )
    assert r.status_code == 200
    got = client.get("/api/2.1/clusters/get?cluster_id=0101-acme-0001")
    assert got.json()["cluster_name"] == "renamed"


def test_delete_cluster(mock: DatabricksMock, client: TestClient) -> None:
    r = client.post("/api/2.1/clusters/delete", json={"cluster_id": "0101-acme-0002"})
    assert r.status_code == 200
    mock.tick()
    got = client.get("/api/2.1/clusters/get?cluster_id=0101-acme-0002")
    assert got.json()["state"] == "TERMINATED"


def test_restart_cluster(mock: DatabricksMock, client: TestClient) -> None:
    r = client.post("/api/2.1/clusters/restart", json={"cluster_id": "0101-acme-0001"})
    assert r.status_code == 200
    assert (
        client.get("/api/2.1/clusters/get?cluster_id=0101-acme-0001").json()["state"]
        == "RESTARTING"
    )
    mock.tick()
    assert (
        client.get("/api/2.1/clusters/get?cluster_id=0101-acme-0001").json()["state"]
        == "PENDING"
    )
    mock.tick()
    assert (
        client.get("/api/2.1/clusters/get?cluster_id=0101-acme-0001").json()["state"]
        == "RUNNING"
    )


def test_clusters_20_get_alias(client: TestClient) -> None:
    r = client.get("/api/2.0/clusters/get?cluster_id=0101-acme-0001")
    assert r.status_code == 200


def test_invalid_json_create(client: TestClient) -> None:
    r = client.post(
        "/api/2.1/clusters/create",
        content=b"not-json",
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 400
    assert r.json()["error_code"] == "INVALID_PARAMETER_VALUE"


def test_stale_page_token_after_write(client: TestClient) -> None:
    first = client.get("/api/2.1/clusters/list?page_size=2")
    token = first.json()["next_page_token"]
    created = client.post("/api/2.1/clusters/create", json={"cluster_name": "extra"})
    assert created.status_code == 200
    stale = client.get(f"/api/2.1/clusters/list?page_size=2&page_token={token}")
    assert stale.status_code == 400
    assert stale.json()["error_code"] == "INVALID_PARAMETER_VALUE"
