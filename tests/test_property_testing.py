"""Property-based tests (Hypothesis). Skipped when hypothesis is not installed."""

import importlib.util

import pytest

from tests.example_models import User, UserQuery

pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("hypothesis") is None,
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

        from semblance import SemblanceAPI
        from semblance.property_testing import strategy_for_input_model
        from semblance.testing import test_client as make_client

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
