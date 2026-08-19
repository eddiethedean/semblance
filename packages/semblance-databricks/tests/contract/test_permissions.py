from fastapi.testclient import TestClient


def test_get_permissions(client: TestClient) -> None:
    r = client.get("/api/2.0/permissions/jobs/1001")
    assert r.status_code == 200
    assert r.json()["object_type"] == "job"


def test_patch_permissions(client: TestClient) -> None:
    r = client.patch(
        "/api/2.0/permissions/jobs/1001",
        json={
            "access_control_list": [
                {
                    "user_name": "other@acme.example",
                    "all_permissions": [{"permission_level": "CAN_VIEW"}],
                }
            ]
        },
    )
    assert r.status_code == 200
    assert r.json()["access_control_list"][0]["user_name"] == "other@acme.example"
