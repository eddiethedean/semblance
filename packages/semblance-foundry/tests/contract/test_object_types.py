from fastapi.testclient import TestClient


def test_list_object_types(client: TestClient) -> None:
    r = client.get("/api/v2/ontologies/acme/objectTypes")
    assert r.status_code == 200
    names = {row["apiName"] for row in r.json()["data"]}
    assert names == {"Employee", "Office"}
    employee = next(x for x in r.json()["data"] if x["apiName"] == "Employee")
    assert employee["primaryKey"] == "employeeId"
    assert "employeeId" in employee["properties"]


def test_list_object_types_pagination(client: TestClient) -> None:
    first = client.get("/api/v2/ontologies/acme/objectTypes?pageSize=1")
    assert first.status_code == 200
    body = first.json()
    assert len(body["data"]) == 1
    token = body["nextPageToken"]
    assert token
    second = client.get(
        f"/api/v2/ontologies/acme/objectTypes?pageSize=1&pageToken={token}"
    )
    assert second.status_code == 200
    assert len(second.json()["data"]) == 1
    assert second.json()["data"][0]["apiName"] != body["data"][0]["apiName"]
    third = client.get(
        "/api/v2/ontologies/acme/objectTypes?pageSize=1&pageToken="
        + (second.json().get("nextPageToken") or "")
    )
    if second.json().get("nextPageToken"):
        assert third.status_code == 200
        assert third.json().get("nextPageToken") in (None, "")


def test_get_object_type(client: TestClient) -> None:
    r = client.get("/api/v2/ontologies/acme/objectTypes/Employee")
    assert r.status_code == 200
    assert r.json()["apiName"] == "Employee"


def test_get_object_type_missing(client: TestClient) -> None:
    r = client.get("/api/v2/ontologies/acme/objectTypes/Nope")
    assert r.status_code == 404
    assert r.json()["errorName"] == "ObjectTypeNotFound"


def test_invalid_page_size(client: TestClient) -> None:
    r = client.get("/api/v2/ontologies/acme/objectTypes?pageSize=0")
    assert r.status_code == 400
    assert r.json()["errorName"] == "InvalidPageSize"
