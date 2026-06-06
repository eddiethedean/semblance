"""Pytest fixtures for Semblance tests.

Tests that need an app typically build a minimal SemblanceAPI and use
test_client(api.as_fastapi()) in the test or a local fixture.
"""

import pytest

from semblance import SemblanceAPI
from tests.example_models import User, UserQuery


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset global rate limiter between tests to avoid cross-test pollution."""
    import semblance.rate_limit as rl

    rl._limiter = None
    yield
    rl._limiter = None


@pytest.fixture
def clean_plugin_registry():
    """Restore plugin registry after tests that register custom links."""
    import semblance.plugins as plugins

    saved = set(plugins._REGISTRY)
    yield
    plugins._REGISTRY.clear()
    plugins._REGISTRY.update(saved)


@pytest.fixture
def users_api() -> SemblanceAPI:
    """Shared API with list and single GET user endpoints."""
    api = SemblanceAPI()
    api.get("/users", input=UserQuery, output=list[User], list_count=2)(lambda: None)
    api.get("/user", input=UserQuery, output=User)(lambda: None)
    return api
