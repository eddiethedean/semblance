"""Tests for PUT, PATCH, DELETE, rate limiting, and response validation."""

import time
from unittest.mock import patch

import pytest
from pydantic import BaseModel, ValidationError

from semblance import SemblanceAPI
from semblance.testing import test_client as make_client
from tests.example_models import User, UserQuery


class UpdateBody(BaseModel):
    name: str = "updated"


class DeletePathInput(BaseModel):
    id: str = ""


class TestPutPatchDelete:
    def test_put_returns_generated_response(self):
        api = SemblanceAPI(seed=42)
        api.put("/users/{id}", input=UpdateBody, output=User)(lambda: None)
        client = make_client(api.as_fastapi())
        r = client.put("/users/abc", json={"name": "put-user"})
        assert r.status_code == 200
        assert r.json()["name"] == "put-user"

    def test_patch_returns_generated_response(self):
        api = SemblanceAPI(seed=42)
        api.patch("/users/{id}", input=UpdateBody, output=User)(lambda: None)
        client = make_client(api.as_fastapi())
        r = client.patch("/users/xyz", json={"name": "patch-user"})
        assert r.status_code == 200
        assert r.json()["name"] == "patch-user"

    def test_delete_204_when_no_output(self):
        api = SemblanceAPI()
        api.delete("/users/{id}", input=DeletePathInput)(lambda: None)
        client = make_client(api.as_fastapi())
        r = client.delete("/users/123")
        assert r.status_code == 204

    def test_delete_200_with_output_model(self):
        api = SemblanceAPI(seed=42)
        api.delete("/users/{id}", input=DeletePathInput, output=User)(lambda: None)
        client = make_client(api.as_fastapi())
        r = client.delete("/users/123")
        assert r.status_code == 200
        assert "name" in r.json()

    def test_openapi_path_params_and_delete_204(self):
        api = SemblanceAPI()
        api.get("/users/{id}", input=DeletePathInput, output=User)(lambda: None)
        api.delete("/users/{id}", input=DeletePathInput)(lambda: None)
        spec = api.as_fastapi().openapi()
        get_params = spec["paths"]["/users/{id}"]["get"]["parameters"]
        assert any(p.get("in") == "path" and p.get("name") == "id" for p in get_params)
        assert "204" in spec["paths"]["/users/{id}"]["delete"]["responses"]


class TestRateLimit:
    def test_rate_limit_returns_429_when_exceeded(self):
        api = SemblanceAPI()
        api.get(
            "/limited",
            input=UserQuery,
            output=list[User],
            rate_limit=2,
        )(lambda: None)
        client = make_client(api.as_fastapi())
        assert client.get("/limited?name=a").status_code == 200
        assert client.get("/limited?name=b").status_code == 200
        assert client.get("/limited?name=c").status_code == 429

    @pytest.mark.slow
    def test_rate_limit_allows_after_window(self):
        api = SemblanceAPI()
        api.get(
            "/limited2",
            input=UserQuery,
            output=list[User],
            rate_limit=1,
        )(lambda: None)
        client = make_client(api.as_fastapi())
        assert client.get("/limited2?name=a").status_code == 200
        assert client.get("/limited2?name=b").status_code == 429
        time.sleep(1.1)
        assert client.get("/limited2?name=c").status_code == 200


class TestValidateResponses:
    def test_validate_responses_does_not_raise_on_valid_response(self):
        api = SemblanceAPI(validate_responses=True)
        api.get("/users", input=UserQuery, output=list[User])(lambda: None)
        client = make_client(api.as_fastapi())
        r = client.get("/users?name=alice")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_validate_responses_raises_on_invalid_output(self):
        api = SemblanceAPI(validate_responses=True)
        api.get("/users", input=UserQuery, output=list[User])(lambda: None)
        client = make_client(api.as_fastapi())

        class BadItem:
            name = 123

        with patch("semblance.api.build_response", return_value=[BadItem()]):
            with pytest.raises(ValidationError):
                client.get("/users?name=x")


@pytest.mark.parametrize(
    "method,match",
    [
        ("get", "Duplicate GET endpoint"),
        ("post", "Duplicate POST endpoint"),
        ("put", "Duplicate PUT endpoint"),
        ("patch", "Duplicate PATCH endpoint"),
        ("delete", "Duplicate DELETE endpoint"),
    ],
)
def test_duplicate_endpoint_raises(method, match):
    class CreateRequest(BaseModel):
        name: str = "x"

    class UpdateBodyLocal(BaseModel):
        name: str = "x"

    class Item(BaseModel):
        id: str = ""
        name: str = ""

    class PathId(BaseModel):
        id: str = ""

    api = SemblanceAPI()
    if method == "get":
        api.get("/users", input=UserQuery, output=list[User])(lambda: None)
        api.get("/users", input=UserQuery, output=list[User])(lambda: None)
    elif method == "post":
        api.post("/users", input=CreateRequest, output=User)(lambda: None)
        api.post("/users", input=CreateRequest, output=User)(lambda: None)
    elif method == "delete":
        api.delete("/users/{id}", input=PathId)(lambda: None)
        api.delete("/users/{id}", input=PathId)(lambda: None)
    elif method == "put":
        api.put("/users/{id}", input=UpdateBodyLocal, output=Item)(lambda: None)
        api.put("/users/{id}", input=UpdateBodyLocal, output=Item)(lambda: None)
    else:
        api.patch("/users/{id}", input=UpdateBodyLocal, output=Item)(lambda: None)
        api.patch("/users/{id}", input=UpdateBodyLocal, output=Item)(lambda: None)
    with pytest.raises(ValueError, match=match):
        api.as_fastapi()
