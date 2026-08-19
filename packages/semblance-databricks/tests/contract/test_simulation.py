from fastapi.testclient import TestClient

from semblance_databricks import DatabricksMock, DatabricksMockConfig
from semblance_databricks.fixtures.loaders import bundled_acme_path


def test_rate_limit_429() -> None:
    mock = DatabricksMock(DatabricksMockConfig(seed=42, rate_limit=2))
    mock.load_fixture(bundled_acme_path())
    client = TestClient(mock.as_fastapi())
    assert client.get("/api/2.1/clusters/list").status_code == 200
    assert client.get("/api/2.1/clusters/list").status_code == 200
    r = client.get("/api/2.1/clusters/list")
    assert r.status_code == 429
    assert r.json()["error_code"] == "REQUEST_LIMIT_EXCEEDED"


def test_error_injection() -> None:
    mock = DatabricksMock(
        DatabricksMockConfig(seed=1, error_rate=1.0, error_codes=[500])
    )
    mock.load_fixture(bundled_acme_path())
    client = TestClient(mock.as_fastapi())
    r = client.get("/api/2.1/clusters/list")
    assert r.status_code == 500
    assert r.json()["error_code"] == "INTERNAL_ERROR"


def test_honors_request_id(client: TestClient) -> None:
    r = client.get(
        "/api/2.1/clusters/list",
        headers={"x-databricks-request-id": "trace-1"},
    )
    assert r.headers["x-databricks-request-id"] == "trace-1"


def test_fail_stage_before_write() -> None:
    mock = DatabricksMock(DatabricksMockConfig(seed=42, fail_stage="before_write"))
    mock.load_fixture(bundled_acme_path())
    client = TestClient(mock.as_fastapi())
    r = client.post("/api/2.1/clusters/create", json={"cluster_name": "x"})
    assert r.status_code == 500
