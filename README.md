# Semblance

[![PyPI](https://img.shields.io/pypi/v/semblance.svg)](https://pypi.org/project/semblance/)
[![Read the Docs](https://readthedocs.org/projects/semblance/badge/?version=latest)](https://semblance.readthedocs.io/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://docs.astral.sh/ruff/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Schema-driven REST API simulation** with FastAPI, Pydantic, and Polyfactory.

Define API behavior declaratively using schemas and dependency metadata—no endpoint logic required. Semblance is built for **contract testing**, **prototyping**, **frontend development**, and **integration testing** against realistic API simulators.

## Features

- **Zero endpoint logic** — Schemas and link metadata define responses
- **FastAPI-native** — Full OpenAPI, validation, async
- **Deterministic** — Seeded generation for reproducible tests
- **Extensible** — Custom link types via plugins
- **Production-ready** — Error simulation, latency, rate limiting, pagination, stateful mode, optional response validation

## Requirements

- Python 3.10+
- FastAPI, Pydantic, Polyfactory, Uvicorn (installed with semblance)

## Installation

```bash
pip install semblance
```

From source (development):

```bash
git clone https://github.com/eddiethedean/semblance.git
cd semblance
pip install -e ".[dev]"
```

## Quick Start

```python
from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel
from semblance import DateRangeFrom, FromInput, SemblanceAPI


class UserQuery(BaseModel):
    name: str = "alice"
    start_date: date = date(2020, 1, 1)
    end_date: date = date(2025, 12, 31)


class User(BaseModel):
    name: Annotated[str, FromInput("name")]
    created_at: Annotated[
        datetime,
        DateRangeFrom("start_date", "end_date"),
    ]


api = SemblanceAPI()


@api.get("/users", input=UserQuery, output=list[User])
def users():
    pass


app = api.as_fastapi()
```

You can register PUT, PATCH, and DELETE endpoints the same way (`@api.put(...)`, `@api.patch(...)`, `@api.delete(..., output=None)` for 204).

Run:

```bash
semblance run app:api --port 8000
# or
uvicorn app:app --reload
```

Try:

```bash
curl "http://127.0.0.1:8000/users?name=alice&start_date=2024-01-01&end_date=2024-12-31"
```

Responses are generated from your output model: `name` comes from the query, `created_at` is random in the date range.

## Use Cases

| Use Case | Description |
|----------|-------------|
| **Contract testing** | Validate client behavior against a schema-accurate mock |
| **Frontend development** | Run a mock API for UI work without a backend |
| **Prototyping** | Ship realistic API shapes before implementation |
| **Integration tests** | Deterministic, isolated API simulators in CI |

## CLI

```bash
# Run a Semblance app
semblance run app:api [--host HOST] [--port PORT] [--reload]

# Export OpenAPI schema (optionally with response examples)
semblance export openapi app:api [-o FILE] [--examples]

# Export OpenAPI + JSON fixtures per endpoint (GET, POST, PUT, PATCH, DELETE)
semblance export fixtures app:api [-o DIR]
```

## Examples

Runnable examples in [examples/](https://semblance.readthedocs.io/en/latest/examples/):

```bash
semblance run examples.basic.app:api --port 8000
semblance run examples.pagination.app:api --port 8000
semblance run examples.nested.app:api --port 8000
semblance run examples.stateful.app:api --port 8000
semblance run examples.advanced.app:api --port 8000
semblance run examples.error_simulation.app:api --port 8000
semblance run examples.plugins.app:api --port 8000
```

| Example | Description |
|---------|-------------|
| [basic](https://semblance.readthedocs.io/en/latest/examples/basic/) | Minimal GET list with FromInput, DateRangeFrom |
| [pagination](https://semblance.readthedocs.io/en/latest/examples/pagination/) | PageParams, PaginatedResponse |
| [nested](https://semblance.readthedocs.io/en/latest/examples/nested/) | Nested model linking |
| [stateful](https://semblance.readthedocs.io/en/latest/examples/stateful/) | POST stores items, GET returns stored list |
| [advanced](https://semblance.readthedocs.io/en/latest/examples/advanced/) | WhenInput, ComputedFrom, filter_by |
| [error_simulation](https://semblance.readthedocs.io/en/latest/examples/error_simulation/) | error_rate, error_codes |
| [plugins](https://semblance.readthedocs.io/en/latest/examples/plugins/) | Custom link (FromEnv) |

## Testing

```python
from semblance import SemblanceAPI, test_client

app = api.as_fastapi()
client = test_client(app)

r = client.get("/users?name=testuser")
assert r.status_code == 200
data = r.json()
assert all(u["name"] == "testuser" for u in data)
```

Deterministic seeding for reproducible tests:

```python
api = SemblanceAPI(seed=42)
# or per-endpoint: seed_from="seed" with a query param
```

## Plugins

Register custom link types:

```python
from semblance import register_link, SemblanceAPI
from typing import Annotated

class FromEnv:
    def __init__(self, env_var: str):
        self.env_var = env_var
    def resolve(self, input_data, rng):
        import os
        return os.environ.get(self.env_var)

register_link(FromEnv)

class User(BaseModel):
    name: Annotated[str, FromEnv("USER_NAME")]
```

## API Overview

| Feature | Description |
|---------|-------------|
| **SemblanceAPI** | GET, POST, PUT, PATCH, DELETE endpoints with input/output models |
| **Links** | FromInput, DateRangeFrom, WhenInput, ComputedFrom |
| **Pagination** | PageParams, PaginatedResponse[T] |
| **Seeding** | `SemblanceAPI(seed=42)` or `seed_from="seed"` |
| **Error simulation** | `error_rate`, `error_codes` |
| **Latency** | `latency_ms`, `jitter_ms` |
| **Rate limiting** | `rate_limit=N` — 429 when exceeded (per endpoint, sliding window) |
| **Filtering** | `filter_by` for list endpoints |
| **Stateful mode** | `SemblanceAPI(stateful=True)` — POST stores; GET (list + by-id), PUT/PATCH/DELETE by id use store |
| **Response validation** | `SemblanceAPI(validate_responses=True)` — verify output conforms to model |
| **OpenAPI** | summary, description, tags on endpoints |
| **Property-based testing** | `semblance.property_testing`: `strategy_for_input_model()`, `test_endpoint()` (Hypothesis) |

## Competitors & Alternatives

| Feature | [Semblance](https://pypi.org/project/semblance/) | [fastapi-mock](https://pypi.org/project/fastapi-mock/) | [Prism](https://stoplight.io/open-source/prism) | [json-server](https://github.com/typicode/json-server) | [Schemathesis](https://schemathesis.readthedocs.io/) | [Mockoon](https://mockoon.com/) |
|---------|:---:|:---:|:---:|:---:|:---:|:---:|
| **Mock API server** | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| **Python / FastAPI native** | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ |
| **Zero endpoint logic** | ✅ | ❌ | ✅ | ✅ | ❌ | ✅ |
| **Realistic example generation** | ✅ | <span title="Uses predefined Pydantic examples or Field defaults, not auto-generated faker-style data">🟡</span> | ✅ | ❌ | ❌ | <span title="Faker templating in rules, but not schema-driven auto-generation">🟡</span> |
| **Input→output binding** | ✅ | ❌ | ❌ | ❌ | ❌ | <span title="Rules can reference request data via templating, but not schema-driven link metadata">🟡</span> |
| **Deterministic seeding** | ✅ | ❌ | ✅ | ❌ | ✅ | <span title="Some dynamic values; true deterministic seeding not primary focus">🟡</span> |
| **Pagination helpers** | ✅ | ❌ | <span title="May derive pagination from OpenAPI examples; no dedicated helpers">🟡</span> | ✅ | ❌ | <span title="Can configure response rules, no built-in pagination helpers">🟡</span> |
| **Error simulation** | ✅ | ❌ | <span title="Can return error responses defined in OpenAPI spec">🟡</span> | ❌ | ❌ | <span title="Rules can return different status codes per condition">🟡</span> |
| **Stateful mode** | ✅ | ❌ | ❌ | ✅ | ❌ | <span title="Rules can simulate state; not true POST-store/GET-return">🟡</span> |
| **Extensible (plugins)** | ✅ | <span title="Middleware-based; custom behavior via decorators or wrappers">🟡</span> | ❌ | ❌ | ✅ | <span title="Templates and response rules provide extensibility">🟡</span> |
| **OpenAPI schema** | ✅ | ✅ | ✅ | ❌ | ✅ | <span title="Can import/export OpenAPI; design is GUI-first, not schema-first">🟡</span> |
| **CI / pytest integration** | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| **Property-based testing** | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ |

🟡 = partial or configurable

## Documentation

Full documentation: **[semblance.readthedocs.io](https://semblance.readthedocs.io/)**

- [Getting Started](https://semblance.readthedocs.io/en/latest/guides/getting-started/)
- [Input and Output Binding](https://semblance.readthedocs.io/en/latest/guides/input-output-binding/)
- [Advanced Links](https://semblance.readthedocs.io/en/latest/guides/advanced-links/)
- [Pagination](https://semblance.readthedocs.io/en/latest/guides/pagination/)
- [Simulation Options](https://semblance.readthedocs.io/en/latest/guides/simulation-options/)
- [Stateful Mode](https://semblance.readthedocs.io/en/latest/guides/stateful-mode/)
- [CLI](https://semblance.readthedocs.io/en/latest/guides/cli/)
- [Plugins](https://semblance.readthedocs.io/en/latest/guides/plugins/)
- [Testing](https://semblance.readthedocs.io/en/latest/guides/testing/)
- [Roadmap](https://semblance.readthedocs.io/en/latest/roadmap/)
- [API Reference](https://semblance.readthedocs.io/en/latest/api/)

## Development

See [CONTRIBUTING.md](https://github.com/eddiethedean/semblance/blob/main/CONTRIBUTING.md) for setup and contribution guidelines.

```bash
git clone https://github.com/eddiethedean/semblance.git
cd semblance
pip install -e ".[dev]"
pytest tests/ -v
```

## License

MIT License.
