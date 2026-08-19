import base64

from fastapi.testclient import TestClient

from semblance_databricks import DatabricksMock, DatabricksMockConfig


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


def test_put_and_read_base64(client: TestClient) -> None:
    payload = base64.b64encode(b"world").decode()
    put = client.post(
        "/api/2.0/dbfs/put",
        json={"path": "/mnt/acme/out.txt", "contents": payload},
    )
    assert put.status_code == 200
    read = client.get("/api/2.0/dbfs/read", params={"path": "/mnt/acme/out.txt"})
    assert base64.b64decode(read.json()["data"]) == b"world"


def test_dbfs_rejects_parent_segments(client: TestClient) -> None:
    r = client.get("/api/2.0/dbfs/list", params={"path": "/mnt/acme/../secret"})
    assert r.status_code == 400


def test_dbfs_temp_dir_stays_sandboxed(tmp_path) -> None:
    mock = DatabricksMock(
        DatabricksMockConfig(seed=42, dbfs_temp_dir=str(tmp_path / "dbfs"))
    )
    mock.load_bundled_fixture()
    client = TestClient(mock.as_fastapi())
    payload = base64.b64encode(b"ok").decode()
    put = client.post(
        "/api/2.0/dbfs/put",
        json={"path": "/safe.txt", "contents": payload},
    )
    assert put.status_code == 200
    written = list((tmp_path / "dbfs").rglob("*"))
    assert any(p.name == "safe.txt" for p in written)
