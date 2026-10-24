# Semblance

[![CI](https://github.com/eddiethedean/semblance/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/eddiethedean/semblance/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/semblance.svg)](https://pypi.org/project/semblance/)
[![Documentation status](https://img.shields.io/readthedocs/semblance/latest.svg)](https://semblance.readthedocs.io/en/latest/)
[![Python versions](https://img.shields.io/pypi/pyversions/semblance.svg)](https://pypi.org/project/semblance/)
[![Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://docs.astral.sh/ruff/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/eddiethedean/semblance/blob/main/LICENSE.md)

**Build a REST API simulator from Pydantic models.**

Semblance turns request and response schemas into a running FastAPI app. Use field metadata to bind responses to request data, generate values within constraints, and simulate failures—without writing endpoint logic.

Build against a mock while the backend takes shape, exercise a client's retry behavior, or run integration tests with repeatable data. FastAPI handles request validation and OpenAPI; Polyfactory generates the response data.

[Documentation](https://semblance.readthedocs.io/en/latest/) · [Capper example](#generate-realistic-data-with-capper) · [Inputs and outputs](#examples) · [Changelog](https://github.com/eddiethedean/semblance/blob/main/CHANGELOG.md) · [Contributing](https://github.com/eddiethedean/semblance/blob/main/CONTRIBUTING.md)

## Quick start

Requires **Python 3.10+**. FastAPI, Pydantic, Polyfactory, and Uvicorn are installed with Semblance.

```bash
pip install semblance
```

Save this as **`app.py`**:

```python
from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel
from semblance import DateRangeFrom, FromInput, SemblanceAPI


class UserQuery(BaseModel):
    name: str = "alice"
    start_date: date = date(2024, 1, 1)
    end_date: date = date(2024, 12, 31)


class User(BaseModel):
    name: Annotated[str, FromInput("name")]
    created_at: Annotated[datetime, DateRangeFrom("start_date", "end_date")]


api = SemblanceAPI(seed=42)


@api.get("/users", input=UserQuery, output=list[User], list_count=2)
def users():
    pass


app = api.as_fastapi()
```

Start the simulator:

```bash
semblance run app:api --port 8000
```

**Input — in another terminal:**

```bash
curl "http://127.0.0.1:8000/users?name=alice"
```

**Output — `200 OK`:**

```json
[
  {"name": "alice", "created_at": "2024-08-22T00:43:29.352128"},
  {"name": "alice", "created_at": "2024-01-10T03:41:40.080943"}
]
```

Change `name`, `start_date`, or `end_date` in the query to change the response. Explore the interactive API docs at [localhost:8000/docs](http://127.0.0.1:8000/docs) or fetch the schema at `/openapi.json`. You can also serve the exported app with `uvicorn app:app --reload`.

## How it works

1. **Describe the request.** An input model defines query, path, or body fields and their Pydantic validation rules.
2. **Describe the response.** An output model defines the response shape. Polyfactory generates fields; `Annotated` links supply values from inputs, other fields, headers, cookies, or JSON fixtures.
3. **Choose the behavior.** Route options control list size, pagination, errors, timing, and authentication. A fixed seed makes generated data repeatable.

In the quick start, `FromInput("name")` copies the requested name and `DateRangeFrom(...)` generates timestamps within the requested range. The function body is a registration placeholder; Semblance ignores it and generates the response from the models.

Register GET, POST, PUT, PATCH, and DELETE routes with the same pattern. Return a model, `list[Model]`, or a pagination wrapper; DELETE with `output=None` returns 204 No Content.

## Generate realistic data with Capper

[Capper](https://github.com/eddiethedean/capper) adds semantic types such as `Name`, `Email`, `Company`, and `City`. Use them in your output model and Semblance's Polyfactory integration automatically generates values with the corresponding Faker providers.

Install the optional dependency:

```bash
pip install "capper[pydantic]"
```

Save this as **`realistic.py`**:

```python
from typing import Annotated

from capper import City, Company, Email, Name
from pydantic import BaseModel
from semblance import FromInput, SemblanceAPI


class CustomerQuery(BaseModel):
    segment: str = "trial"
    seed: int = 42


class Customer(BaseModel):
    name: Name
    email: Email
    company: Company
    city: City
    segment: Annotated[str, FromInput("segment")]


api = SemblanceAPI()


@api.get("/customer", input=CustomerQuery, output=Customer, seed_from="seed")
def customer():
    pass
```

Run `semblance run realistic:api --port 8002`.

**Input:**

```bash
curl "http://127.0.0.1:8002/customer?segment=enterprise&seed=42"
```

**Output — `200 OK`:**

```json
{
  "name": "Allison Hill",
  "email": "donaldgarcia@example.net",
  "company": "Miller, Henderson and Johnson",
  "city": "East William",
  "segment": "enterprise"
}
```

The query supplies `segment`; Capper generates the other fields. Change `seed` to generate another customer, or repeat it for the same result with the same dependency versions. This response was captured with Capper 1.1.1, Faker 40.43.0, and Polyfactory 3.5.0. Capper fields are generated independently; use `ComputedFrom` or custom links when fields need to depend on one another.

## Test without a server

Install the test dependencies:

```bash
pip install pytest httpx
```

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
```

The input is `GET /users?name=testuser`. The test client calls the app in process and receives **`200 OK`** with:

```json
[
  {"name": "testuser", "created_at": "2024-08-22T00:43:29.352128"},
  {"name": "testuser", "created_at": "2024-01-10T03:41:40.080943"}
]
```

Run `pytest -q test_app.py`. The result is `1 passed` (timing varies). Use `seed_from="seed"` on a route to take a per-request seed from an input field, or add Hypothesis for [property-based tests](https://semblance.readthedocs.io/en/latest/guides/testing/).

## Simulate failure and recovery

Test a client that should recover after a temporary outage. Save this as **`resilience.py`**, reusing the models from `app.py`:

```python
from app import User, UserQuery
from semblance import ScenarioStep, SemblanceAPI

api = SemblanceAPI(seed=42)


@api.get(
    "/users",
    input=UserQuery,
    output=list[User],
    list_count=2,
    scenario=(
        ScenarioStep(status=503, detail="Temporarily unavailable"),
        ScenarioStep(status=200),
    ),
)
def users():
    pass
```

Run `semblance run resilience:api --port 8001`.

**First input:**

```bash
curl "http://127.0.0.1:8001/users?name=alice"
```

**Output — `503 Service Unavailable`:**

```json
{"detail": "Temporarily unavailable"}
```

**Second input — repeat the same request:**

```bash
curl "http://127.0.0.1:8001/users?name=alice"
```

**Output — `200 OK`:**

```json
[
  {"name": "alice", "created_at": "2024-08-22T00:43:29.352128"},
  {"name": "alice", "created_at": "2024-01-10T03:41:40.080943"}
]
```

Subsequent requests also return generated users. Each route holds its final scenario step until the simulator is restarted.

For other failure modes, use `ErrorCase` to match validated input, `error_rate` and `error_codes` for random failures, or `latency_ms`, `jitter_ms`, and `rate_limit` to exercise slow requests and throttling. See [simulation options](https://semblance.readthedocs.io/en/latest/guides/simulation-options/).

## Capabilities

| Need | Semblance provides |
| --- | --- |
| Bind responses to requests | `FromInput`, `FromHeader`, and `FromCookie` |
| Express field relationships | `DateRangeFrom`, `WhenInput`, and `ComputedFrom`, including nested models |
| Reuse fixture data | `FromJsonFixture` and `FromNestedFixture`, with variants and optional strict matching |
| Generate repeatable data | Global `seed` or per-request `seed_from`; fixed or input-driven `list_count` |
| Page through results | `PageParams` / `PaginatedResponse[T]` for offset pagination; `PageTable` / `PageSlice[T]` for token-keyed pages |
| Keep state across requests | `SemblanceAPI(stateful=True)` stores POST results for list, lookup, PUT, PATCH, and DELETE routes |
| Exercise failure handling | `ErrorCase`, `ScenarioStep`, random errors, latency, jitter, and rate limits |
| Simulate protected routes | A per-route `bearer_tokens` allow-list; invalid or missing tokens return 401 |
| Validate contracts | Pydantic request validation, optional `validate_responses=True` and `validate_links=True`, and OpenAPI export |
| Integrate with existing apps | `as_fastapi()`, `mount_into(...)`, and middleware support |
| Extend generation and testing | Custom links via `register_link`, pytest fixtures, and Hypothesis helpers |

State and rate limits live in memory within a process. Use stateful mode for local workflows and tests; restarting the simulator clears its store. See the [stateful CRUD example](https://semblance.readthedocs.io/en/latest/examples/stateful_crud/) for a complete create, read, update, and delete flow.

## CLI

Use the CLI to scaffold, validate, serve, and export a simulator:

```bash
# Create app.py and semblance.yaml in a new project directory
semblance init --with-config

# Check route definitions and field links without starting a server
semblance validate app:api

# Serve with automatic reload during development
semblance run app:api --port 8000 --reload

# Export OpenAPI, including generated response examples
semblance export openapi app:api --examples -o openapi.json

# Export OpenAPI and JSON response fixtures
semblance export fixtures app:api -o fixtures
```

| Command | Output or result |
| --- | --- |
| `semblance init --with-config` | Writes `app.py` and `semblance.yaml`, printing their absolute paths and a run command |
| `semblance validate app:api` | Prints `OK` and exits with status 0 when the routes and links are valid |
| `semblance run app:api --port 8000 --reload` | Starts the simulator at `http://127.0.0.1:8000`; `/docs` shows the registered routes |
| `semblance export openapi app:api --examples -o openapi.json` | Prints `Wrote openapi.json`; the file contains the `/users` schema and example responses |
| `semblance export fixtures app:api -o fixtures` | Prints `Wrote fixtures to fixtures`; the directory contains OpenAPI and JSON response fixtures |

See the [CLI guide](https://semblance.readthedocs.io/en/latest/guides/cli/) for all options and the [concepts guide](https://semblance.readthedocs.io/en/latest/guides/concepts/) for configuration defaults.

## Examples

From a clone of this repository, run an example with:

```bash
semblance run examples.basic.app:api --port 8000
```

Replace `basic` with any module below:

| Module | Demonstrates |
| --- | --- |
| [basic](https://semblance.readthedocs.io/en/latest/examples/basic/) | Input bindings and generated date ranges |
| [pagination](https://semblance.readthedocs.io/en/latest/examples/pagination/) | Paginated response models |
| [nested](https://semblance.readthedocs.io/en/latest/examples/nested/) | Links in nested models |
| [advanced](https://semblance.readthedocs.io/en/latest/examples/advanced/) | Conditional links, computed fields, and filtering |
| [stateful](https://semblance.readthedocs.io/en/latest/examples/stateful/) | Store created items and list them |
| [stateful_crud](https://semblance.readthedocs.io/en/latest/examples/stateful_crud/) | Full CRUD with an in-memory store |
| [put_patch_delete](https://semblance.readthedocs.io/en/latest/examples/put_patch_delete/) | Generated PUT, PATCH, and DELETE responses |
| [error_simulation](https://semblance.readthedocs.io/en/latest/examples/error_simulation/) | Seeded success, 404, and 503 responses |
| [request_links](https://semblance.readthedocs.io/en/latest/examples/request_links/) | Header and cookie bindings |
| [plugins](https://semblance.readthedocs.io/en/latest/examples/plugins/) | Custom link types |

Expand an example below for its inputs and captured outputs. Start one example server at a time on port 8000. Generated values can change with dependency versions; use the IDs returned by your running server when following a stateful sequence.

<details>
<summary>basic — input bindings and date ranges</summary>

[Source](https://github.com/eddiethedean/semblance/blob/main/examples/basic/app.py) · [Guide](https://semblance.readthedocs.io/en/latest/examples/basic/)

**Input:**

```bash
curl -sS 'http://127.0.0.1:8000/users?name=alice&start_date=2024-01-01&end_date=2024-12-31'
```

**Output — `200 OK`:**

```json
[
  {"name": "alice", "created_at": "2024-08-22T00:43:29.352128"},
  {"name": "alice", "created_at": "2024-01-10T03:41:40.080943"}
]
```

</details>

<details>
<summary>pagination — limit, offset, and total</summary>

[Source](https://github.com/eddiethedean/semblance/blob/main/examples/pagination/app.py) · [Guide](https://semblance.readthedocs.io/en/latest/examples/pagination/)

This example generates a pool of `limit` items, so `limit=3` and `offset=0` return three items with `total=3`.

**Input:**

```bash
curl -sS 'http://127.0.0.1:8000/users?limit=3&offset=0&name=alice'
```

**Output — `200 OK`:**

```json
{
  "items": [
    {
      "name": "alice"
    },
    {
      "name": "alice"
    },
    {
      "name": "alice"
    }
  ],
  "total": 3,
  "limit": 3,
  "offset": 0
}
```

</details>

<details>
<summary>nested — request data inside a nested response</summary>

[Source](https://github.com/eddiethedean/semblance/blob/main/examples/nested/app.py) · [Guide](https://semblance.readthedocs.io/en/latest/examples/nested/)

The city is bound to the request. This module uses plain `str` fields for street and ZIP; the Capper example above demonstrates how semantic types improve generated data.

**Input:**

```bash
curl -sS 'http://127.0.0.1:8000/user?name=foo&city=Boston'
```

**Output — `200 OK`:**

```json
{
  "name": "foo",
  "address": {
    "street": "HbolMJUevblAbkHClEQa",
    "city": "Boston",
    "zip": "PKriXrefSFPLBYtCRGSE"
  }
}
```

</details>

<details>
<summary>advanced — conditional, computed, and filtered fields</summary>

[Source](https://github.com/eddiethedean/semblance/blob/main/examples/advanced/app.py) · [Guide](https://semblance.readthedocs.io/en/latest/examples/advanced/)

**Input 1:**

```bash
curl -sS 'http://127.0.0.1:8000/user/status?name=alice&include_status=true&status=active'
```

**Output — `200 OK`:**

```json
{"name": "alice", "status": "active"}
```

**Input 2:**

```bash
curl -sS 'http://127.0.0.1:8000/user/fullname?first=Jane&last=Smith'
```

**Output — `200 OK`:**

```json
{"first": "Jane", "last": "Smith", "full": "Jane Smith"}
```

**Input 3:**

```bash
curl -sS 'http://127.0.0.1:8000/users?name=x&status=active&include_status=true'
```

**Output — `200 OK`:**

```json
[
  {"name": "x", "status": "active"},
  {"name": "x", "status": "active"},
  {"name": "x", "status": "active"}
]
```

</details>

<details>
<summary>stateful — create an item, then list stored items</summary>

[Source](https://github.com/eddiethedean/semblance/blob/main/examples/stateful/app.py) · [Guide](https://semblance.readthedocs.io/en/latest/examples/stateful/)

Run against a fresh server, in the order shown. Generated IDs can vary; the same ID appears in the stored list.

**Input 1:**

```bash
curl -sS -X POST http://127.0.0.1:8000/users -H 'Content-Type: application/json' -d '{"name": "alice"}'
```

**Output — `200 OK`:**

```json
{"id": "HbolMJUevblAbkHClEQa", "name": "alice"}
```

**Input 2:**

```bash
curl -sS http://127.0.0.1:8000/users
```

**Output — `200 OK`:**

```json
[
  {"id": "HbolMJUevblAbkHClEQa", "name": "alice"}
]
```

</details>

<details>
<summary>stateful_crud — create, read, replace, patch, list, and delete</summary>

[Source](https://github.com/eddiethedean/semblance/blob/main/examples/stateful_crud/app.py) · [Guide](https://semblance.readthedocs.io/en/latest/examples/stateful_crud/)

Run against a fresh server, in the order shown. Use the ID returned by POST in subsequent paths; the sample below uses `HbolMJUevblAbkHClEQa`.

**Input 1:**

```bash
curl -sS -X POST http://127.0.0.1:8000/users -H 'Content-Type: application/json' -d '{"name": "alice"}'
```

**Output — `200 OK`:**

```json
{"id": "HbolMJUevblAbkHClEQa", "name": "alice"}
```

**Input 2:**

```bash
curl -sS http://127.0.0.1:8000/users/HbolMJUevblAbkHClEQa
```

**Output — `200 OK`:**

```json
{"id": "HbolMJUevblAbkHClEQa", "name": "alice"}
```

**Input 3:**

```bash
curl -sS -X PUT http://127.0.0.1:8000/users/HbolMJUevblAbkHClEQa -H 'Content-Type: application/json' -d '{"name": "alice-replaced"}'
```

**Output — `200 OK`:**

```json
{"id": "HbolMJUevblAbkHClEQa", "name": "alice-replaced"}
```

**Input 4:**

```bash
curl -sS -X PATCH http://127.0.0.1:8000/users/HbolMJUevblAbkHClEQa -H 'Content-Type: application/json' -d '{"name": "alice-updated"}'
```

**Output — `200 OK`:**

```json
{"id": "HbolMJUevblAbkHClEQa", "name": "alice-updated"}
```

**Input 5:**

```bash
curl -sS http://127.0.0.1:8000/users
```

**Output — `200 OK`:**

```json
[
  {"id": "HbolMJUevblAbkHClEQa", "name": "alice-updated"}
]
```

**Input 6:**

```bash
curl -sS -X DELETE http://127.0.0.1:8000/users/HbolMJUevblAbkHClEQa
```

**Output — `204 No Content`:**

No response body.

**Input 7:**

```bash
curl -sS http://127.0.0.1:8000/users/HbolMJUevblAbkHClEQa
```

**Output — `404 Not Found`:**

```json
{"detail": "Not found"}
```

</details>

<details>
<summary>put_patch_delete — generated responses for write methods</summary>

[Source](https://github.com/eddiethedean/semblance/blob/main/examples/put_patch_delete/app.py) · [Guide](https://semblance.readthedocs.io/en/latest/examples/put_patch_delete/)

These routes generate responses without storing them. The output `id` is a generated string, so it does not echo the path ID.

**Input 1:**

```bash
curl -sS -X PUT http://127.0.0.1:8000/users/abc -H 'Content-Type: application/json' -d '{"name": "put-user"}'
```

**Output — `200 OK`:**

```json
{"id": "HbolMJUevblAbkHClEQa", "name": "put-user"}
```

**Input 2:**

```bash
curl -sS -X PATCH http://127.0.0.1:8000/users/xyz -H 'Content-Type: application/json' -d '{"name": "patch-user"}'
```

**Output — `200 OK`:**

```json
{"id": "HbolMJUevblAbkHClEQa", "name": "patch-user"}
```

**Input 3:**

```bash
curl -sS -X DELETE http://127.0.0.1:8000/users/123
```

**Output — `204 No Content`:**

No response body.

**Input 4:**

```bash
curl -sS -X DELETE http://127.0.0.1:8000/users/123/with-body
```

**Output — `200 OK`:**

```json
{"id": "HbolMJUevblAbkHClEQa", "name": "PKriXrefSFPLBYtCRGSE"}
```

</details>

<details>
<summary>error_simulation — successful and failing responses</summary>

[Source](https://github.com/eddiethedean/semblance/blob/main/examples/error_simulation/app.py) · [Guide](https://semblance.readthedocs.io/en/latest/examples/error_simulation/)

With the bundled `SemblanceAPI(seed=99)`, this request consistently succeeds. The other fixed seeds below reproduce the configured failure responses. To sample failures across repeated requests, use `SemblanceAPI()` without a fixed seed.

**Input 1:**

```bash
curl -sS 'http://127.0.0.1:8000/users?name=alice'
```

**Output — `200 OK`:**

```json
[
  {"name": "alice"},
  {"name": "alice"}
]
```

For this input, restart the example after changing its constructor to `SemblanceAPI(seed=1)`.

**Input 2:**

```bash
curl -sS 'http://127.0.0.1:8000/users?name=alice'
```

**Output — `404 Not Found`:**

```json
{"detail": "Simulated error"}
```

For this input, restart the example after changing its constructor to `SemblanceAPI(seed=8)`.

**Input 3:**

```bash
curl -sS 'http://127.0.0.1:8000/users?name=alice'
```

**Output — `503 Service Unavailable`:**

```json
{"detail": "Simulated error"}
```

</details>

<details>
<summary>request_links — query, header, and cookie inputs</summary>

[Source](https://github.com/eddiethedean/semblance/blob/main/examples/request_links/app.py) · [Guide](https://semblance.readthedocs.io/en/latest/examples/request_links/)

**Input:**

```bash
curl -sS 'http://127.0.0.1:8000/user?name=alice' -H 'X-Request-Id: id-1' -H 'Cookie: session_id=sess-1'
```

**Output — `200 OK`:**

```json
{"name": "alice", "request_id": "id-1", "session": "sess-1"}
```

</details>

<details>
<summary>plugins — environment data and a custom link</summary>

[Source](https://github.com/eddiethedean/semblance/blob/main/examples/plugins/app.py) · [Guide](https://semblance.readthedocs.io/en/latest/examples/plugins/)

Start this module with its environment input set:

```bash
USER_NAME=DocBot semblance run examples.plugins.app:api --port 8000
```

**Input:**

```bash
curl -sS 'http://127.0.0.1:8000/user?role=admin'
```

**Output — `200 OK`:**

```json
{"name": "DocBot", "role": "admin"}
```

</details>

## Optional API adapters

Separate packages simulate selected operations of external APIs using bundled or custom fixtures:

| Package | Coverage | Install |
| --- | --- | --- |
| [semblance-foundry](https://github.com/eddiethedean/semblance/blob/main/packages/semblance-foundry/README.md) | Selected Foundry API v2 ontology-read operations | `pip install semblance-foundry` |
| [semblance-databricks](https://github.com/eddiethedean/semblance/blob/main/packages/semblance-databricks/README.md) | Selected Databricks workspace REST operations | `pip install semblance-databricks` |

Both adapters are unofficial, independently versioned test doubles. Their package READMEs document supported operations, authentication modes, and compatibility limits.

## Documentation

Start with [Getting started](https://semblance.readthedocs.io/en/latest/guides/getting-started/) or choose a guide:

- **Models and links:** [Input and output binding](https://semblance.readthedocs.io/en/latest/guides/input-output-binding/), [advanced links](https://semblance.readthedocs.io/en/latest/guides/advanced-links/), [request links](https://semblance.readthedocs.io/en/latest/guides/request-links/), and [plugins](https://semblance.readthedocs.io/en/latest/guides/plugins/).
- **Behavior:** [Pagination](https://semblance.readthedocs.io/en/latest/guides/pagination/), [stateful mode](https://semblance.readthedocs.io/en/latest/guides/stateful-mode/), and [simulation options](https://semblance.readthedocs.io/en/latest/guides/simulation-options/).
- **Testing and reference:** [Testing](https://semblance.readthedocs.io/en/latest/guides/testing/), [cookbook](https://semblance.readthedocs.io/en/latest/guides/cookbook/), [troubleshooting](https://semblance.readthedocs.io/en/latest/guides/troubleshooting/), and [API reference](https://semblance.readthedocs.io/en/latest/api/).
- **Project direction:** [Roadmap](https://semblance.readthedocs.io/en/latest/roadmap/) and [changelog](https://github.com/eddiethedean/semblance/blob/main/CHANGELOG.md).

## Development

Set up all three packages from a clean clone:

```bash
git clone https://github.com/eddiethedean/semblance.git
cd semblance
python -m venv .venv
source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pip install -e "packages/semblance-foundry[dev]"
pip install -e "packages/semblance-databricks[dev]"

pytest tests/ -v -m "not sdk"
pytest packages/semblance-foundry/tests -v -m "not sdk"
pytest packages/semblance-databricks/tests -v -m "not sdk"
```

See [CONTRIBUTING.md](https://github.com/eddiethedean/semblance/blob/main/CONTRIBUTING.md) for lint, type, security, and documentation checks. Report vulnerabilities through the process in [SECURITY.md](https://github.com/eddiethedean/semblance/blob/main/SECURITY.md).

## License

[MIT](https://github.com/eddiethedean/semblance/blob/main/LICENSE.md).
