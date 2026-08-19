import base64

from fastapi.testclient import TestClient


def test_list_dbfs(client: TestClient) -> None:
    r = client.get("/api/2.0/dbfs/list", params={"path": "/mnt/acme"})
    assert r.status_code == 200
    paths = [f["path"] for f in r.json()["files"]]
    assert "/mnt/acme/readme.txt" in paths


def test_read_dbfs(client: TestClient) -> None:
    r = client.get("/api/2.0/dbfs/read", params={"path": "/mnt/acme/readme.txt"})
    assert r.status_code == 200
    data = base64.b64decode(r.json()["data"])
    assert data == b"hello"
