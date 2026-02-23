"""Tests for Phase 5: PUT/PATCH/DELETE, rate limiting, response validation, property-based testing."""

import time

import pytest
from pydantic import BaseModel

from semblance import SemblanceAPI
from semblance.testing import test_client as make_client
from tests.example_models import User, UserQuery


class UpdateBody(BaseModel):
    """Minimal body for PUT/PATCH."""

    name: str = "updated"


class DeletePathInput(BaseModel):
    """Path-only input for DELETE (e.g. id from path)."""

    id: str = ""


# --- PUT / PATCH / DELETE ---


class TestPutPatchDelete:
    def test_put_returns_generated_response(self):
        api = SemblanceAPI(seed=42)
        api.put("/users/{id}", input=UpdateBody, output=User)(lambda: None)
        app = api.as_fastapi()
        client = make_client(app)
        r = client.put("/users/abc", json={"name": "put-user"})
        assert r.status_code == 200
        data = r.json()
        assert "name" in data
        assert data["name"] == "put-user"

    def test_patch_returns_generated_response(self):
        api = SemblanceAPI(seed=42)
        api.patch("/users/{id}", input=UpdateBody, output=User)(lambda: None)
        app = api.as_fastapi()
        client = make_client(app)
        r = client.patch("/users/xyz", json={"name": "patch-user"})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "patch-user"

    def test_delete_204_when_no_output(self):
        api = SemblanceAPI()
        api.delete("/users/{id}", input=DeletePathInput)(lambda: None)
        app = api.as_fastapi()
        client = make_client(app)
        r = client.delete("/users/123")
        assert r.status_code == 204
        assert r.content in (b"", b" ")

    def test_delete_200_with_output_model(self):
        api = SemblanceAPI(seed=42)
        api.delete("/users/{id}", input=DeletePathInput, output=User)(lambda: None)
        app = api.as_fastapi()
        client = make_client(app)
        r = client.delete("/users/123")
        assert r.status_code == 200
        data = r.json()
        assert "name" in data


# --- Rate limiting ---


class TestRateLimit:
    def test_rate_limit_returns_429_when_exceeded(self):
        api = SemblanceAPI()
        api.get(
            "/limited",
            input=UserQuery,
            output=list[User],
            rate_limit=2,
        )(lambda: None)
        app = api.as_fastapi()
        client = make_client(app)
        r1 = client.get("/limited?name=a")
        r2 = client.get("/limited?name=b")
        r3 = client.get("/limited?name=c")
        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r3.status_code == 429

    def test_rate_limit_allows_after_window(self):
        api = SemblanceAPI()
        api.get(
            "/limited2",
            input=UserQuery,
            output=list[User],
            rate_limit=1,
        )(lambda: None)
        app = api.as_fastapi()
        client = make_client(app)
        assert client.get("/limited2?name=a").status_code == 200
        assert client.get("/limited2?name=b").status_code == 429
        time.sleep(1.1)
        assert client.get("/limited2?name=c").status_code == 200


# --- Response validation ---


class TestValidateResponses:
    def test_validate_responses_does_not_raise_on_valid_response(self):
        api = SemblanceAPI(validate_responses=True)
        api.get("/users", input=UserQuery, output=list[User])(lambda: None)
        app = api.as_fastapi()
        client = make_client(app)
        r = client.get("/users?name=alice")
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# --- Property-based testing ---


@pytest.mark.skipif(
    __import__("importlib.util").util.find_spec("hypothesis") is None,
    reason="hypothesis not installed",
)
class TestPropertyBased:
    def test_strategy_for_input_model_generates_valid_instances(self):
        from hypothesis import given

        from semblance.property_testing import strategy_for_input_model

        strategy = strategy_for_input_model(UserQuery)

        @given(strategy)
        def run(inp):
            assert isinstance(inp, UserQuery)
            parsed = UserQuery.model_validate(inp.model_dump())
            assert parsed.name == inp.name

        run()

    def test_test_endpoint_get_validates_responses(self):
        from hypothesis import given
        from pydantic import TypeAdapter

        from semblance.property_testing import strategy_for_input_model

        api = SemblanceAPI(seed=42)
        api.get("/users", input=UserQuery, output=list[User], list_count=2)(
            lambda: None
        )
        app = api.as_fastapi()
        client = make_client(app)
        strategy = strategy_for_input_model(UserQuery)

        @given(strategy)
        def run(inp):
            r = client.get("/users", params=inp.model_dump())
            assert r.status_code == 200
            TypeAdapter(list[User]).validate_python(r.json())

        run()
