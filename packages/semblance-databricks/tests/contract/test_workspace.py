from fastapi.testclient import TestClient


def test_get_status(client: TestClient) -> None:
    r = client.get(
        "/api/2.0/workspace/get-status",
        params={"path": "/Users/user@acme.example/notebook"},
    )
    assert r.status_code == 200
    assert r.json()["object_type"] == "NOTEBOOK"


def test_get_status_missing(client: TestClient) -> None:
    r = client.get("/api/2.0/workspace/get-status", params={"path": "/missing"})
    assert r.status_code == 404
    assert r.json()["error_code"] == "RESOURCE_DOES_NOT_EXIST"


def test_me(client: TestClient) -> None:
    r = client.get("/api/2.0/preview/scim/v2/Me")
    assert r.status_code == 200
    assert r.json()["userName"] == "user@acme.example"
