# Testing

Use Semblance's test client to send requests directly to a FastAPI app. No server process or listening port is needed. Start with the `app.py` from [Getting started](getting-started.md).

## Install the test dependencies

```bash
pip install pytest httpx2
```

## Test a response and invalid input

Save this beside `app.py` as **`test_app.py`**:

```python
from datetime import datetime

from app import app
from semblance import test_client as make_test_client


def test_users():
    with make_test_client(app) as client:
        response = client.get("/users", params={"name": "testuser"})

    assert response.status_code == 200
    users = response.json()
    assert len(users) == 2
    assert all(user["name"] == "testuser" for user in users)
    assert all(
        datetime(2024, 1, 1)
        <= datetime.fromisoformat(user["created_at"])
        < datetime(2025, 1, 1)
        for user in users
    )


def test_invalid_date():
    with make_test_client(app) as client:
        response = client.get("/users", params={"start_date": "not-a-date"})

    assert response.status_code == 422
```

Run:

```bash
pytest -q test_app.py
```

**Output:** `2 passed` (timing varies). The first request returns `200 OK`:

```json
[
  {"name": "testuser", "created_at": "2024-08-22T00:43:29.352128"},
  {"name": "testuser", "created_at": "2024-01-10T03:41:40.080943"}
]
```

The alias `make_test_client` keeps pytest from collecting the imported helper as a test. Using it as a context manager also runs FastAPI's lifespan hooks and closes the client.

## Reuse a client with a fixture

For a larger test suite, put this fixture in **`conftest.py`** beside `app.py`. Tests can then accept a `client` argument:

```python
import pytest

from app import app
from semblance import test_client as make_test_client


@pytest.fixture
def client():
    with make_test_client(app) as client:
        yield client
```

## Reproduce generated data

Choose a seed based on what the test needs:

| Configuration | Behavior |
|---|---|
| `SemblanceAPI(seed=42)` | Uses the same global seed for generated data on every request |
| `SemblanceAPI()` with `seed_from="seed"` on a route | Reads the seed from that route's validated input |
| No global or request seed | Generated values can vary between requests |

A global seed takes precedence over `seed_from`. Exact generated values can change when Polyfactory, Faker, or semantic-type dependencies change; keep dependency versions fixed for snapshots. Assert on response shape and field relationships when exact text is unimportant.

This complete example compares two requests with the same seed. Save it as **`seeded.py`** and run `python seeded.py`:

```python
from pydantic import BaseModel
from semblance import SemblanceAPI, test_client as make_test_client


class Query(BaseModel):
    seed: int = 42


class Result(BaseModel):
    value: int


api = SemblanceAPI()


@api.get("/result", input=Query, output=Result, seed_from="seed")
def result():
    pass


with make_test_client(api.as_fastapi()) as client:
    first = client.get("/result?seed=42")
    second = client.get("/result?seed=42")
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
```

Successful execution exits with status 0 and no output.

## Test many inputs with Hypothesis

Install Hypothesis:

```bash
pip install hypothesis
```

Save this standalone test as **`test_properties.py`**:

```python
from typing import Annotated

from pydantic import BaseModel
from semblance import FromInput, SemblanceAPI, test_client as make_test_client
from semblance.property_testing import (
    strategy_for_input_model,
    test_endpoint as check_endpoint,
)


class EchoQuery(BaseModel):
    name: str


class EchoResponse(BaseModel):
    name: Annotated[str, FromInput("name")]


def test_many_names():
    api = SemblanceAPI(seed=42)
    api.get("/user", input=EchoQuery, output=EchoResponse)(lambda: None)

    with make_test_client(api.as_fastapi()) as client:
        check_endpoint(
            client,
            "GET",
            "/user",
            strategy_for_input_model(EchoQuery),
            EchoResponse,
            invariants=(lambda request, body: body["name"] == request.name,),
        )
```

`pytest -q test_properties.py` reports `1 passed`. `check_endpoint` generates inputs, checks successful statuses, validates the response model, and checks each invariant. Assertion failures include a request you can use to reproduce the problem.

`strategy_for_input_model` handles common field types. For models with constrained fields or relationships between inputs, provide your own Hypothesis strategy through `input_strategy`, for example `st.builds(YourModel, ...)`.

## Keep state and failure tests isolated

- Create a fresh `SemblanceAPI` for each test that advances a scenario or rate limit.
- Use `api.clear_store()` or `api.clear_store("/users")` between stateful test cases.
- Use [ScenarioStep](simulation-options.md#scenario-steps) for a known sequence such as 503 followed by 200. Fixed seeds also repeat random error selection when `error_rate` is enabled.
- Assert `422` for malformed input and test configured `ErrorCase` responses separately.
