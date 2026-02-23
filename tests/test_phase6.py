"""Tests for Phase 6: Stateful CRUD, export PUT/PATCH/DELETE, OpenAPI 429/error docs."""

import json
import tempfile
from pathlib import Path

from pydantic import BaseModel

from semblance import SemblanceAPI
from semblance.testing import test_client as make_client
from tests.example_models import User, UserQuery


class ItemWithId(BaseModel):
    """Model with id for stateful CRUD."""

    id: str = ""
    name: str = ""


class UpdateBody(BaseModel):
    name: str = "updated"


class PathIdInput(BaseModel):
    id: str = ""


# --- Stateful GET by id ---


class TestStatefulGetById:
    def test_stateful_get_by_id_returns_stored_item(self):
        api = SemblanceAPI(seed=42, stateful=True)
        api.post("/items", input=ItemWithId, output=ItemWithId)(lambda: None)
        api.get("/items", input=UserQuery, output=list[ItemWithId])(lambda: None)
        api.get("/items/{id}", input=PathIdInput, output=ItemWithId)(lambda: None)
        app = api.as_fastapi()
        client = make_client(app)
        r_post = client.post("/items", json={"name": "first"})
        assert r_post.status_code == 200
        created = r_post.json()
        assert "id" in created
        item_id = created["id"]
        r_get = client.get(f"/items/{item_id}")
        assert r_get.status_code == 200
        assert r_get.json()["id"] == item_id

    def test_stateful_get_by_id_404_when_missing(self):
        api = SemblanceAPI(stateful=True)
        api.get("/items/{id}", input=PathIdInput, output=ItemWithId)(lambda: None)
        app = api.as_fastapi()
        client = make_client(app)
        r = client.get("/items/nonexistent")
        assert r.status_code == 404

    def test_stateful_get_by_id_404_verbose_detail(self):
        api = SemblanceAPI(stateful=True, verbose_errors=True)
        api.get("/items/{id}", input=PathIdInput, output=ItemWithId)(lambda: None)
        app = api.as_fastapi()
        client = make_client(app)
        r = client.get("/items/nonexistent")
        assert r.status_code == 404
        data = r.json()
        assert data["detail"]["collection"] == "/items"
        assert data["detail"]["id_field"] == "id"
        assert data["detail"]["id_value"] == "nonexistent"


# --- Stateful PUT (upsert) ---


class TestStatefulPut:
    def test_stateful_put_creates_new(self):
        api = SemblanceAPI(seed=42, stateful=True)
        api.put("/items/{id}", input=UpdateBody, output=ItemWithId)(lambda: None)
        api.get("/items", input=UserQuery, output=list[ItemWithId])(lambda: None)
        app = api.as_fastapi()
        client = make_client(app)
        r = client.put("/items/new-1", json={"name": "created"})
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == "new-1"
        r_list = client.get("/items")
        assert len(r_list.json()) == 1

    def test_stateful_put_updates_existing(self):
        api = SemblanceAPI(seed=42, stateful=True)
        api.post("/items", input=ItemWithId, output=ItemWithId)(lambda: None)
        api.put("/items/{id}", input=UpdateBody, output=ItemWithId)(lambda: None)
        api.get("/items", input=UserQuery, output=list[ItemWithId])(lambda: None)
        app = api.as_fastapi()
        client = make_client(app)
        r_post = client.post("/items", json={"name": "original"})
        assert r_post.status_code == 200
        item_id = r_post.json()["id"]
        r = client.put(f"/items/{item_id}", json={"name": "updated"})
        assert r.status_code == 200
        r_list = client.get("/items")
        assert len(r_list.json()) == 1
        assert r_list.json()[0]["id"] == item_id


# --- Stateful PATCH ---


class TestStatefulPatch:
    def test_stateful_patch_updates_existing(self):
        api = SemblanceAPI(seed=42, stateful=True)
        api.post("/items", input=ItemWithId, output=ItemWithId)(lambda: None)
        api.patch("/items/{id}", input=UpdateBody, output=ItemWithId)(lambda: None)
        app = api.as_fastapi()
        client = make_client(app)
        r_post = client.post("/items", json={"name": "before"})
        assert r_post.status_code == 200
        item_id = r_post.json()["id"]
        r = client.patch(f"/items/{item_id}", json={"name": "after"})
        assert r.status_code == 200
        assert r.json()["id"] == item_id

    def test_stateful_patch_404_when_missing(self):
        api = SemblanceAPI(stateful=True)
        api.patch("/items/{id}", input=UpdateBody, output=ItemWithId)(lambda: None)
        app = api.as_fastapi()
        client = make_client(app)
        r = client.patch("/items/missing", json={"name": "x"})
        assert r.status_code == 404


# --- Stateful DELETE ---


class TestStatefulDelete:
    def test_stateful_delete_removes_and_returns_204(self):
        api = SemblanceAPI(seed=42, stateful=True)
        api.post("/items", input=ItemWithId, output=ItemWithId)(lambda: None)
        api.delete("/items/{id}", input=PathIdInput)(lambda: None)
        api.get("/items", input=UserQuery, output=list[ItemWithId])(lambda: None)
        app = api.as_fastapi()
        client = make_client(app)
        r_post = client.post("/items", json={"name": "to delete"})
        assert r_post.status_code == 200
        item_id = r_post.json()["id"]
        r = client.delete(f"/items/{item_id}")
        assert r.status_code == 204
        r_list = client.get("/items")
        assert len(r_list.json()) == 0

    def test_stateful_delete_404_when_missing(self):
        api = SemblanceAPI(stateful=True)
        api.delete("/items/{id}", input=PathIdInput)(lambda: None)
        app = api.as_fastapi()
        client = make_client(app)
        r = client.delete("/items/nonexistent")
        assert r.status_code == 404


# --- Export PUT/PATCH/DELETE ---


class TestExportPutPatchDelete:
    def test_export_fixtures_includes_put_patch_delete(self):
        api = SemblanceAPI(seed=42)
        api.get("/users", input=UserQuery, output=list[User])(lambda: None)
        api.put("/users/{id}", input=UpdateBody, output=User)(lambda: None)
        app = api.as_fastapi()
        with tempfile.TemporaryDirectory() as tmp:
            from semblance.export import export_fixtures

            export_fixtures(app, Path(tmp))
            files = list(Path(tmp).iterdir())
            names = [f.name for f in files]
            assert "openapi.json" in names
            assert any("PUT" in n for n in names)
            put_file = next(f for f in files if "PUT" in f.name)
            data = json.loads(put_file.read_text())
            assert "name" in data or isinstance(data, dict)

    def test_export_openapi_with_examples_put_patch_delete(self):
        api = SemblanceAPI(seed=42)
        api.put("/users/{id}", input=UpdateBody, output=User)(lambda: None)
        app = api.as_fastapi()
        from semblance.export import export_openapi

        schema = export_openapi(app, include_examples=True)
        paths = schema.get("paths", {})
        users_path = paths.get("/users/{id}", {})
        put_op = users_path.get("put")
        assert put_op is not None
        responses = put_op.get("responses", {})
        assert "200" in responses or "201" in responses


# --- OpenAPI 429 and error codes ---


class TestOpenAPIResponses:
    def test_openapi_includes_429_when_rate_limit_set(self):
        api = SemblanceAPI()
        api.get(
            "/limited",
            input=UserQuery,
            output=list[User],
            rate_limit=10,
        )(lambda: None)
        app = api.as_fastapi()
        schema = app.openapi()
        paths = schema.get("paths", {})
        op = paths.get("/limited", {}).get("get")
        assert op is not None
        assert "429" in op.get("responses", {})

    def test_openapi_includes_error_codes_when_error_rate_set(self):
        api = SemblanceAPI()
        api.get(
            "/errors",
            input=UserQuery,
            output=list[User],
            error_rate=0.1,
            error_codes=[404, 500],
        )(lambda: None)
        app = api.as_fastapi()
        schema = app.openapi()
        paths = schema.get("paths", {})
        op = paths.get("/errors", {}).get("get")
        assert op is not None
        responses = op.get("responses", {})
        assert "404" in responses
        assert "500" in responses
