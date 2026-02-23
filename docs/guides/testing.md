# Testing

Semblance is built for testing. Use the test client with pytest for fast, deterministic API tests.

## test_client

```python
from semblance import SemblanceAPI, test_client

api = SemblanceAPI()
@api.get("/users", input=UserQuery, output=list[User])(lambda: None)
app = api.as_fastapi()
client = test_client(app)

r = client.get("/users?name=testuser")
assert r.status_code == 200
data = r.json()
assert all(u["name"] == "testuser" for u in data)
# data: [{"name": "testuser", "created_at": "2024-08-21T09:22:43.516168"}, ...]
```

`test_client` wraps your FastAPI app in Starlette's `TestClient`. No server process is started.

## Deterministic Seeding

Use a fixed seed for reproducible tests:

```python
api = SemblanceAPI(seed=42)
```

Or per-request via `seed_from`:

```python
class UserQueryWithSeed(BaseModel):
    name: str = "alice"
    seed: int | None = None

@api.get("/users", input=UserQueryWithSeed, output=list[User], seed_from="seed")
def users():
    pass

# Same seed → same responses
r1 = client.get("/users?name=x&seed=99")
r2 = client.get("/users?name=x&seed=99")
assert r1.json()[0]["created_at"] == r2.json()[0]["created_at"]
```

## Pytest Fixture

```python
# conftest.py
import pytest
from semblance import SemblanceAPI, test_client

@pytest.fixture
def api():
    api = SemblanceAPI(seed=42)
    api.get("/users", input=UserQuery, output=list[User])(lambda: None)
    return api

@pytest.fixture
def client(api):
    return test_client(api.as_fastapi())

# test_users.py
def test_users_return_list(client):
    r = client.get("/users?name=alice")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
```

## Property-based Testing

For Schemathesis-style testing, use Hypothesis with Semblance's property-testing helpers (requires `hypothesis`, included in `[dev]`):

```python
from hypothesis import given
from semblance import SemblanceAPI
from semblance.property_testing import strategy_for_input_model
from semblance.testing import test_client

api = SemblanceAPI(seed=42)
api.get("/users", input=UserQuery, output=list[User], list_count=2)(lambda: None)
app = api.as_fastapi()
client = test_client(app)
strategy = strategy_for_input_model(UserQuery)

@given(strategy)
def test_users_valid_response(inp):
    r = client.get("/users", params=inp.model_dump())
    assert r.status_code == 200
    from pydantic import TypeAdapter
    TypeAdapter(list[User]).validate_python(r.json())

test_users_valid_response()
```

- **strategy_for_input_model(model, path_template=None)** — builds a Hypothesis strategy that generates instances of the input model (handles `Annotated`, optional fields, nested models).
- **test_endpoint(client, method, path, input_strategy, output_model, ...)** — runs a `@given` test: draws input, calls the endpoint, asserts status and validates response; supports optional invariants.

Use property-based tests to ensure many generated inputs produce valid responses and to catch schema drift.

## Contract and Snapshot Testing

- Assert response shape matches your output model.
- Use deterministic seeds for snapshot-style checks.
- Test validation: send invalid input and assert `422` responses.
