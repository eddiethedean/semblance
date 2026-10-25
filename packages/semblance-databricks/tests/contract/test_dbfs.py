import base64

from fastapi.testclient import TestClient

from semblance_databricks import DatabricksMock, DatabricksMockConfig
from semblance_databricks.services.dbfs import routes as dbfs_routes


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


def test_read_rejects_negative_offset(client: TestClient) -> None:
    r = client.get(
        "/api/2.0/dbfs/read",
        params={"path": "/mnt/acme/readme.txt", "offset": -1},
    )
    assert r.status_code == 400


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


def test_dbfs_failed_disk_write_does_not_commit_memory(tmp_path) -> None:
    dbfs_root = tmp_path / "dbfs"
    dbfs_root.mkdir()
    (dbfs_root / "blocked").write_bytes(b"parent file")
    mock = DatabricksMock(
        DatabricksMockConfig(seed=42, dbfs_temp_dir=str(dbfs_root))
    )
    client = TestClient(mock.as_fastapi(), raise_server_exceptions=False)
    revision = mock.state.revision

    put = client.post(
        "/api/2.0/dbfs/put",
        json={
            "path": "/blocked/child.txt",
            "contents": base64.b64encode(b"new").decode(),
        },
    )

    assert put.status_code == 500
    assert "/blocked/child.txt" not in mock.state.dbfs
    assert mock.state.revision == revision
    read = client.get(
        "/api/2.0/dbfs/read", params={"path": "/blocked/child.txt"}
    )
    assert read.status_code == 404
    assert (dbfs_root / "blocked").read_bytes() == b"parent file"


def test_dbfs_failed_disk_replace_preserves_existing_file(tmp_path, monkeypatch) -> None:
    dbfs_root = tmp_path / "dbfs"
    mock = DatabricksMock(
        DatabricksMockConfig(seed=42, dbfs_temp_dir=str(dbfs_root))
    )
    client = TestClient(mock.as_fastapi(), raise_server_exceptions=False)
    path = "/existing.txt"
    disk_path = dbfs_root / "existing.txt"
    old_contents = b"before"

    initial_put = client.post(
        "/api/2.0/dbfs/put",
        json={"path": path, "contents": base64.b64encode(old_contents).decode()},
    )
    assert initial_put.status_code == 200
    revision = mock.state.revision

    def fail_replace(source: str | bytes, destination: str | bytes) -> None:
        raise OSError("simulated disk replace failure")

    monkeypatch.setattr(dbfs_routes.os, "replace", fail_replace)
    failed_put = client.post(
        "/api/2.0/dbfs/put",
        json={"path": path, "contents": base64.b64encode(b"after").decode()},
    )

    assert failed_put.status_code == 500
    assert mock.state.dbfs[path].data == old_contents
    assert mock.state.revision == revision
    assert disk_path.read_bytes() == old_contents
    assert list(dbfs_root.glob(".existing.txt.*")) == []
