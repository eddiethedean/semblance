from fastapi.testclient import TestClient


def test_list_objects(client: TestClient) -> None:
    r = client.get("/api/v2/ontologies/acme/objects/Employee")
    assert r.status_code == 200
    data = r.json()["data"]
    assert len(data) == 4
    assert data[0]["employeeId"] == "1"
    assert data[0]["__primaryKey"] == "1"
    assert "__rid" in data[0]


def test_list_objects_pagination(client: TestClient) -> None:
    first = client.get("/api/v2/ontologies/acme/objects/Employee?pageSize=2")
    body = first.json()
    assert len(body["data"]) == 2
    token = body["nextPageToken"]
    second = client.get(
        f"/api/v2/ontologies/acme/objects/Employee?pageSize=2&pageToken={token}"
    )
    assert len(second.json()["data"]) == 2
    assert second.json().get("nextPageToken") in (None, "")
    ids = [row["employeeId"] for row in body["data"] + second.json()["data"]]
    assert ids == ["1", "2", "3", "4"]


def test_list_objects_select(client: TestClient) -> None:
    r = client.get(
        "/api/v2/ontologies/acme/objects/Employee",
        params=[("select", "name")],
    )
    row = r.json()["data"][0]
    assert "name" in row
    assert "employeeId" in row
    assert "officeId" not in row


def test_get_object(client: TestClient) -> None:
    r = client.get("/api/v2/ontologies/acme/objects/Employee/1")
    assert r.status_code == 200
    assert r.json()["name"] == "Ada Lovelace"


def test_get_object_missing(client: TestClient) -> None:
    r = client.get("/api/v2/ontologies/acme/objects/Employee/999")
    assert r.status_code == 404
    assert r.json()["errorName"] == "ObjectNotFound"


def test_tampered_page_token(client: TestClient) -> None:
    r = client.get("/api/v2/ontologies/acme/objects/Employee?pageToken=not-a-token")
    assert r.status_code == 400
    assert r.json()["errorName"] == "InvalidPageToken"
