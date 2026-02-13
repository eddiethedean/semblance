# Semblance

[![PyPI](https://img.shields.io/pypi/v/semblance.svg)](https://pypi.org/project/semblance/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Schema-driven REST API simulation** with FastAPI, Pydantic, and Polyfactory.

Define API behavior declaratively using schemas and dependency metadata—no endpoint logic required. Semblance is built for **contract testing**, **prototyping**, **frontend development**, and **integration testing** against realistic API simulators.

## Features

- **Zero endpoint logic** — Schemas and link metadata define responses
- **FastAPI-native** — Full OpenAPI, validation, async
- **Deterministic** — Seeded generation for reproducible tests
- **Extensible** — Custom link types via plugins
- **Production-ready** — Error simulation, latency, pagination, stateful mode

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

# Export JSON fixtures per endpoint
semblance export fixtures app:api [-o DIR]
```

## Examples

Runnable examples in [examples/](examples/):

```bash
semblance run examples.basic.app:api --port 8000
semblance run examples.pagination.app:api --port 8000
semblance run examples.nested.app:api --port 8000
semblance run examples.stateful.app:api --port 8000
semblance run examples.advanced.app:api --port 8000
```

| Example | Description |
|---------|-------------|
| [basic](examples/basic/) | Minimal GET list with FromInput, DateRangeFrom |
| [pagination](examples/pagination/) | PageParams, PaginatedResponse |
| [nested](examples/nested/) | Nested model linking |
| [stateful](examples/stateful/) | POST stores items, GET returns stored list |
| [advanced](examples/advanced/) | WhenInput, ComputedFrom, filter_by |

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
| **SemblanceAPI** | GET and POST endpoints with input/output models |
| **Links** | FromInput, DateRangeFrom, WhenInput, ComputedFrom |
| **Pagination** | PageParams, PaginatedResponse[T] |
| **Seeding** | `SemblanceAPI(seed=42)` or `seed_from="seed"` |
| **Error simulation** | `error_rate`, `error_codes` |
| **Latency** | `latency_ms`, `jitter_ms` |
| **Filtering** | `filter_by` for list endpoints |
| **Stateful mode** | `SemblanceAPI(stateful=True)` — POST stores, GET returns stored |
| **OpenAPI** | summary, description, tags on endpoints |

## Documentation

- [Getting Started](docs/guides/getting-started.md)
- [Input and Output Binding](docs/guides/input-output-binding.md)
- [Advanced Links](docs/guides/advanced-links.md)
- [Pagination](docs/guides/pagination.md)
- [Testing](docs/guides/testing.md)
- [Simulation Options](docs/guides/simulation-options.md)
- [Stateful Mode](docs/guides/stateful-mode.md)
- [Roadmap](docs/roadmap.md)
- [API Reference](docs/api/index.md)

## Development

```bash
git clone https://github.com/eddiethedean/semblance.git
cd semblance
pip install -e ".[dev]"
pytest tests/ -v
```

## License

MIT License.
