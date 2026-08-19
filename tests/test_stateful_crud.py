"""Tests for stateful CRUD mode."""

import tempfile
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel

from semblance import FromInput, SemblanceAPI
from semblance.testing import test_client as make_client
from tests.example_models import User, UserQuery


class ItemWithId(BaseModel):
    id: str = ""
    name: Annotated[str, FromInput("name")] = ""


class UpdateBody(BaseModel):
    name: str = "updated"


class PathIdInput(BaseModel):
    id: str = ""


def test_stateful_mode_post_and_list():
    class CreateUser(BaseModel):
        name: str

    class UserWithId(BaseModel):
        id: str = ""
        name: Annotated[str, FromInput("name")]

    api = SemblanceAPI(stateful=True)
    api.post("/users", input=CreateUser, output=UserWithId)(lambda: None)
    api.get("/users", input=CreateUser, output=list[UserWithId])(lambda: None)
    client = make_client(api.as_fastapi())
    api.clear_store("/users")

    r1 = client.post("/users", json={"name": "alice"})
    assert r1.status_code == 200
    u1 = r1.json()
    assert u1["name"] == "alice"
    assert u1["id"]

    r2 = client.get("/users?name=x")
    assert len(r2.json()) == 1
    assert r2.json()[0]["id"] == u1["id"]

    client.post("/users", json={"name": "bob"})
    assert len(client.get("/users?name=x").json()) == 2


class TestStatefulGetById:
    def test_stateful_get_by_id_returns_stored_item(self):
        api = SemblanceAPI(seed=42, stateful=True)
        api.post("/items", input=ItemWithId, output=ItemWithId)(lambda: None)
        api.get("/items", input=UserQuery, output=list[ItemWithId])(lambda: None)
        api.get("/items/{id}", input=PathIdInput, output=ItemWithId)(lambda: None)
        client = make_client(api.as_fastapi())
        created = client.post("/items", json={"name": "first"}).json()
        item_id = created["id"]
        r_get = client.get(f"/items/{item_id}")
        assert r_get.status_code == 200
        assert r_get.json()["id"] == item_id

    def test_stateful_get_by_id_404_when_missing(self):
        api = SemblanceAPI(stateful=True)
        api.get("/items/{id}", input=PathIdInput, output=ItemWithId)(lambda: None)
        client = make_client(api.as_fastapi())
        assert client.get("/items/nonexistent").status_code == 404

    def test_stateful_get_by_id_404_verbose_detail(self):
        api = SemblanceAPI(stateful=True, verbose_errors=True)
        api.get("/items/{id}", input=PathIdInput, output=ItemWithId)(lambda: None)
        client = make_client(api.as_fastapi())
        r = client.get("/items/nonexistent")
        assert r.status_code == 404
        data = r.json()
        assert data["detail"]["collection"] == "/items"
        assert data["detail"]["id_field"] == "id"
        assert data["detail"]["id_value"] == "nonexistent"


class TestStatefulPut:
    def test_stateful_put_creates_new(self):
        api = SemblanceAPI(seed=42, stateful=True)
        api.put("/items/{id}", input=UpdateBody, output=ItemWithId)(lambda: None)
        api.get("/items", input=UserQuery, output=list[ItemWithId])(lambda: None)
        client = make_client(api.as_fastapi())
        r = client.put("/items/new-1", json={"name": "created"})
        assert r.status_code == 200
        assert r.json()["id"] == "new-1"
        assert len(client.get("/items").json()) == 1

    def test_stateful_put_updates_existing(self):
        api = SemblanceAPI(seed=42, stateful=True)
        api.post("/items", input=ItemWithId, output=ItemWithId)(lambda: None)
        api.put("/items/{id}", input=UpdateBody, output=ItemWithId)(lambda: None)
        api.get("/items", input=UserQuery, output=list[ItemWithId])(lambda: None)
        client = make_client(api.as_fastapi())
        item_id = client.post("/items", json={"name": "original"}).json()["id"]
        r = client.put(f"/items/{item_id}", json={"name": "updated"})
        assert r.status_code == 200
        assert r.json()["name"] == "updated"
        listed = client.get("/items").json()
        assert len(listed) == 1
        assert listed[0]["id"] == item_id
        assert listed[0]["name"] == "updated"


class TestStatefulPatch:
    def test_stateful_patch_updates_existing(self):
        api = SemblanceAPI(seed=42, stateful=True)
        api.post("/items", input=ItemWithId, output=ItemWithId)(lambda: None)
        api.patch("/items/{id}", input=UpdateBody, output=ItemWithId)(lambda: None)
        client = make_client(api.as_fastapi())
        item_id = client.post("/items", json={"name": "before"}).json()["id"]
        r = client.patch(f"/items/{item_id}", json={"name": "after"})
        assert r.status_code == 200
        assert r.json()["id"] == item_id
        assert r.json()["name"] == "after"

    def test_stateful_patch_404_when_missing(self):
        api = SemblanceAPI(stateful=True)
        api.patch("/items/{id}", input=UpdateBody, output=ItemWithId)(lambda: None)
        client = make_client(api.as_fastapi())
        assert client.patch("/items/missing", json={"name": "x"}).status_code == 404


class TestStatefulDelete:
    def test_stateful_delete_removes_and_returns_204(self):
        api = SemblanceAPI(seed=42, stateful=True)
        api.post("/items", input=ItemWithId, output=ItemWithId)(lambda: None)
        api.delete("/items/{id}", input=PathIdInput)(lambda: None)
        api.get("/items", input=UserQuery, output=list[ItemWithId])(lambda: None)
        client = make_client(api.as_fastapi())
        item_id = client.post("/items", json={"name": "to delete"}).json()["id"]
        assert client.delete(f"/items/{item_id}").status_code == 204
        assert len(client.get("/items").json()) == 0

    def test_stateful_delete_404_when_missing(self):
        api = SemblanceAPI(stateful=True)
        api.delete("/items/{id}", input=PathIdInput)(lambda: None)
        client = make_client(api.as_fastapi())
        assert client.delete("/items/nonexistent").status_code == 404


class TestExportPutPatchDelete:
    def test_export_fixtures_includes_put_patch_delete(self):
        api = SemblanceAPI(seed=42)
        api.get("/users", input=UserQuery, output=list[User])(lambda: None)
        api.put("/users/{id}", input=UpdateBody, output=User)(lambda: None)
        app = api.as_fastapi()
        with tempfile.TemporaryDirectory() as tmp:
            from semblance.export import export_fixtures

            export_fixtures(app, Path(tmp))
            names = [f.name for f in Path(tmp).iterdir()]
            assert "openapi.json" in names
            assert any("PUT" in n for n in names)

    def test_export_openapi_with_examples_put_patch_delete(self):
        api = SemblanceAPI(seed=42)
        api.put("/users/{id}", input=UpdateBody, output=User)(lambda: None)
        from semblance.export import export_openapi

        schema = export_openapi(api.as_fastapi(), include_examples=True)
        put_op = schema["paths"]["/users/{id}"]["put"]
        responses = put_op.get("responses", {})
        assert "200" in responses or "201" in responses


class TestOpenAPIResponses:
    def test_openapi_includes_429_when_rate_limit_set(self):
        api = SemblanceAPI()
        api.get(
            "/limited",
            input=UserQuery,
            output=list[User],
            rate_limit=10,
        )(lambda: None)
        op = api.as_fastapi().openapi()["paths"]["/limited"]["get"]
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
        responses = api.as_fastapi().openapi()["paths"]["/errors"]["get"]["responses"]
        assert "404" in responses
        assert "500" in responses


def test_stateful_get_by_int_id():
    class CreateItem(BaseModel):
        name: str

    class Item(BaseModel):
        id: int = 0
        name: Annotated[str, FromInput("name")]

    class PathId(BaseModel):
        id: str = ""

    api = SemblanceAPI(stateful=True, seed=1)
    api.post("/items", input=CreateItem, output=Item)(lambda: None)
    api.get("/items/{id}", input=PathId, output=Item)(lambda: None)
    client = make_client(api.as_fastapi())
    created = client.post("/items", json={"name": "widget"})
    assert created.status_code == 200
    item_id = created.json()["id"]
    got = client.get(f"/items/{item_id}")
    assert got.status_code == 200
    assert got.json()["name"] == "widget"
