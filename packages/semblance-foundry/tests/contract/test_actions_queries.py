from fastapi.testclient import TestClient


def test_list_action_types(client: TestClient) -> None:
    r = client.get("/api/v2/ontologies/acme/actionTypes")
    assert r.status_code == 200
    names = {row["apiName"] for row in r.json()["data"]}
    assert "renameEmployee" in names


def test_get_action_type(client: TestClient) -> None:
    r = client.get("/api/v2/ontologies/acme/actionTypes/renameEmployee")
    assert r.status_code == 200
    assert r.json()["apiName"] == "renameEmployee"


def test_list_query_types(client: TestClient) -> None:
    r = client.get("/api/v2/ontologies/acme/queryTypes")
    assert r.status_code == 200
    names = {row["apiName"] for row in r.json()["data"]}
    assert "employeesByOffice" in names


def test_get_query_type(client: TestClient) -> None:
    r = client.get("/api/v2/ontologies/acme/queryTypes/employeesByOffice")
    assert r.status_code == 200
    assert r.json()["apiName"] == "employeesByOffice"


def test_execute_query(client: TestClient) -> None:
    r = client.post(
        "/api/v2/ontologies/acme/queries/employeesByOffice/execute",
        json={"parameters": {"officeId": "hq"}},
    )
    assert r.status_code == 200
    body = r.json()
    assert "data" in body
    assert body["data"][0]["employeeId"] == "1"
