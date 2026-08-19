from fastapi.testclient import TestClient


def test_list_jobs(client: TestClient) -> None:
    r = client.get("/api/2.2/jobs/list")
    assert r.status_code == 200
    jobs = r.json()["jobs"]
    assert len(jobs) >= 2
    assert "job_id" in jobs[0]
    assert "settings" in jobs[0]
    assert "created_time" in jobs[0]
    assert "creator_user_name" in jobs[0]


def test_get_job(client: TestClient) -> None:
    r = client.get("/api/2.2/jobs/get?job_id=1001")
    assert r.status_code == 200
    assert r.json()["settings"]["name"] == "nightly-etl"


def test_create_job(client: TestClient) -> None:
    r = client.post("/api/2.2/jobs/create", json={"name": "adhoc"})
    assert r.status_code == 200
    jid = r.json()["job_id"]
    got = client.get(f"/api/2.2/jobs/get?job_id={jid}")
    assert got.json()["settings"]["name"] == "adhoc"


def test_reset_job(client: TestClient) -> None:
    r = client.post(
        "/api/2.2/jobs/reset",
        json={"job_id": 1002, "new_settings": {"name": "renamed-job"}},
    )
    assert r.status_code == 200
    got = client.get("/api/2.2/jobs/get?job_id=1002")
    assert got.json()["settings"]["name"] == "renamed-job"


def test_delete_job(client: TestClient) -> None:
    created = client.post("/api/2.2/jobs/create", json={"name": "tmp"})
    jid = created.json()["job_id"]
    deleted = client.post("/api/2.2/jobs/delete", json={"job_id": jid})
    assert deleted.status_code == 200
    missing = client.get(f"/api/2.2/jobs/get?job_id={jid}")
    assert missing.status_code == 404


def test_jobs_21_alias(client: TestClient) -> None:
    r = client.get("/api/2.1/jobs/list")
    assert r.status_code == 200
    assert len(r.json()["jobs"]) >= 2
