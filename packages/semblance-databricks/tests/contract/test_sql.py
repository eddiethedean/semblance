from fastapi.testclient import TestClient

from semblance_databricks import DatabricksMock, DatabricksMockConfig


def test_execute_statement(client: TestClient) -> None:
    r = client.post(
        "/api/2.0/sql/statements",
        json={"warehouse_id": "wh-acme", "statement": "SELECT 1"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"]["state"] == "SUCCEEDED"
    assert body["result"]["data_array"] == [["ok"]]
    sid = body["statement_id"]
    got = client.get(f"/api/2.0/sql/statements/{sid}")
    assert got.status_code == 200


def test_get_statement(client: TestClient) -> None:
    created = client.post(
        "/api/2.0/sql/statements",
        json={"warehouse_id": "wh-acme", "statement": "SELECT 1"},
    )
    sid = created.json()["statement_id"]
    r = client.get(f"/api/2.0/sql/statements/{sid}")
    assert r.status_code == 200
    assert r.json()["statement_id"] == sid


def test_statement_callback() -> None:
    mock = DatabricksMock(DatabricksMockConfig(seed=42))
    mock.load_bundled_fixture()
    mock.register_statement(
        "SELECT n",
        lambda body, state: {"chunks": [[["a"]], [["b"]]]},
    )
    client = TestClient(mock.as_fastapi())
    r = client.post(
        "/api/2.0/sql/statements",
        json={"warehouse_id": "wh-acme", "statement": "SELECT n"},
    )
    assert r.json()["result"]["data_array"] == [["a"]]
    assert r.json()["result"]["next_chunk_internal"] == 1


def test_execute_requires_warehouse(client: TestClient) -> None:
    r = client.post("/api/2.0/sql/statements", json={"statement": "SELECT 1"})
    assert r.status_code == 400
    assert r.json()["error_code"] == "INVALID_PARAMETER_VALUE"
