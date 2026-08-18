from fastapi.testclient import TestClient

from semblance_foundry.testing import FoundryMockContext


def test_exit_criterion_http_flow(client: TestClient) -> None:
    first = client.get("/api/v2/ontologies/acme/objects/Employee?pageSize=2")
    assert first.status_code == 200
    token = first.json()["nextPageToken"]
    second = client.get(
        f"/api/v2/ontologies/acme/objects/Employee?pageSize=2&pageToken={token}"
    )
    assert second.status_code == 200
    assert len(first.json()["data"]) == 2
    assert len(second.json()["data"]) == 2

    got = client.get("/api/v2/ontologies/acme/objects/Employee/1")
    assert got.status_code == 200
    assert got.json()["name"] == "Ada Lovelace"

    linked = client.get("/api/v2/ontologies/acme/objects/Employee/1/links/worksAt")
    assert linked.status_code == 200
    assert linked.json()["data"][0]["officeId"] == "hq"

    query = client.post(
        "/api/v2/ontologies/acme/queries/employeesByOffice/execute",
        json={"parameters": {}},
    )
    assert query.status_code == 200
    assert query.json()["data"][0]["employeeId"] == "1"


def test_context_resets_state() -> None:
    with FoundryMockContext(seed=42) as client:
        client.get("/api/v2/ontologies")
    with FoundryMockContext(seed=42) as client:
        r = client.get("/api/v2/ontologies/acme/objects/Employee")
        assert r.status_code == 200
        assert len(r.json()["data"]) == 4
