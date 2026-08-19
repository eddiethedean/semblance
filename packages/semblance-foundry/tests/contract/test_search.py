from fastapi.testclient import TestClient


def test_search_eq(client: TestClient) -> None:
    r = client.post(
        "/api/v2/ontologies/acme/objects/Employee/search",
        json={"where": {"type": "eq", "field": "officeId", "value": "hq"}},
    )
    assert r.status_code == 200
    ids = {row["employeeId"] for row in r.json()["data"]}
    assert ids == {"1", "2"}


def test_search_and(client: TestClient) -> None:
    r = client.post(
        "/api/v2/ontologies/acme/objects/Employee/search",
        json={
            "where": {
                "type": "and",
                "value": [
                    {"type": "eq", "field": "officeId", "value": "hq"},
                    {"type": "eq", "field": "employeeId", "value": "1"},
                ],
            }
        },
    )
    assert r.status_code == 200
    assert [row["employeeId"] for row in r.json()["data"]] == ["1"]


def test_search_unsupported_filter(client: TestClient) -> None:
    r = client.post(
        "/api/v2/ontologies/acme/objects/Employee/search",
        json={"where": {"type": "or", "value": []}},
    )
    assert r.status_code == 400
    assert r.json()["errorName"] == "InvalidQuery"


def test_search_page_token_does_not_reuse_across_filters(client: TestClient) -> None:
    first = client.post(
        "/api/v2/ontologies/acme/objects/Employee/search",
        json={
            "pageSize": 1,
            "where": {"type": "eq", "field": "officeId", "value": "hq"},
        },
    )
    token = first.json().get("nextPageToken")
    assert token
    reused = client.post(
        "/api/v2/ontologies/acme/objects/Employee/search",
        json={
            "pageSize": 1,
            "pageToken": token,
            "where": {"type": "eq", "field": "officeId", "value": "other"},
        },
    )
    assert reused.status_code == 400
