from fastapi.testclient import TestClient


def test_list_warehouses(client: TestClient) -> None:
    r = client.get("/api/2.0/sql/warehouses")
    assert r.status_code == 200
    assert r.json()["warehouses"][0]["id"] == "wh-acme"


def test_get_warehouse(client: TestClient) -> None:
    r = client.get("/api/2.0/sql/warehouses/wh-acme")
    assert r.status_code == 200
    assert r.json()["name"] == "analytics"


def test_create_delete_warehouse(client: TestClient) -> None:
    created = client.post("/api/2.0/sql/warehouses", json={"name": "scratch"})
    assert created.status_code == 200
    wid = created.json()["id"]
    got = client.get(f"/api/2.0/sql/warehouses/{wid}")
    assert got.status_code == 200
    deleted = client.delete(f"/api/2.0/sql/warehouses/{wid}")
    assert deleted.status_code == 200
    missing = client.get(f"/api/2.0/sql/warehouses/{wid}")
    assert missing.status_code == 404
