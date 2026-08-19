from fastapi.testclient import TestClient


def test_cluster_events(client: TestClient) -> None:
    r = client.post("/api/2.1/clusters/events", json={"cluster_id": "0101-acme-0001"})
    assert r.status_code == 200
    assert r.json()["total_count"] >= 1
    assert r.json()["events"][0]["type"]
