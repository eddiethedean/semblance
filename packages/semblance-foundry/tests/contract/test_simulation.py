from fastapi.testclient import TestClient

from semblance_foundry import FoundryMock, FoundryMockConfig
from semblance_foundry.fixtures.loaders import bundled_acme_path


def test_rate_limit_429() -> None:
    mock = FoundryMock(FoundryMockConfig(seed=42, rate_limit=2))
    mock.load_fixture(bundled_acme_path())
    client = TestClient(mock.as_fastapi())
    assert client.get("/api/v2/ontologies").status_code == 200
    assert client.get("/api/v2/ontologies").status_code == 200
    r = client.get("/api/v2/ontologies")
    assert r.status_code == 429
    assert r.json()["errorName"] == "RateLimitExceeded"


def test_error_injection() -> None:
    mock = FoundryMock(FoundryMockConfig(seed=1, error_rate=1.0, error_codes=[500]))
    mock.load_fixture(bundled_acme_path())
    client = TestClient(mock.as_fastapi())
    r = client.get("/api/v2/ontologies")
    assert r.status_code == 500
    assert r.json()["errorName"] == "InjectedError"


def test_honors_request_id(client: TestClient) -> None:
    r = client.get("/api/v2/ontologies", headers={"X-Request-ID": "trace-1"})
    assert r.headers["X-Request-ID"] == "trace-1"


def test_add_objects_and_query_callback() -> None:
    mock = FoundryMock(FoundryMockConfig(seed=42))
    mock.load_fixture(bundled_acme_path())
    mock.ontologies.add_objects(
        ontology="acme",
        object_type="Employee",
        objects=[{"employeeId": "9", "name": "New", "officeId": "hq"}],
    )
    mock.register_query(
        "employeesByOffice",
        lambda params, state: {"data": [{"ok": True, "n": params.get("n")}]},
    )
    client = TestClient(mock.as_fastapi())
    listed = client.get("/api/v2/ontologies/acme/objects/Employee").json()["data"]
    assert any(row["employeeId"] == "9" for row in listed)
    r = client.post(
        "/api/v2/ontologies/acme/queries/employeesByOffice/execute",
        json={"parameters": {"n": 3}},
    )
    assert r.json()["data"][0]["ok"] is True
    assert r.json()["data"][0]["n"] == 3
