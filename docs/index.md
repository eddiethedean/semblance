# Semblance

**Schema-driven REST API simulation** with FastAPI, Pydantic, and Polyfactory.

Semblance lets you define API behavior declaratively using schemas alone. Input models, output models, and relationships between them fully determine API responses — **no endpoint logic required**.

> *A semblance is the appearance or form of something — not the thing itself.*  
> Semblance creates APIs that look and behave real enough to test, prototype, and integrate against.

## Quick Start

```bash
pip install semblance
```

Create `app.py`:

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

Example output (with `SemblanceAPI(seed=42)` and `list_count=2`):

```json
[
  {"name": "alice", "created_at": "2024-08-21T09:22:43.516168"},
  {"name": "alice", "created_at": "2024-01-10T03:05:39.176702"}
]
```

## Features

- **Zero endpoint logic** — schemas drive behavior
- **Schema-driven** — input/output models and links define responses
- **Full HTTP methods** — GET, POST, PUT, PATCH, DELETE with input/output models
- **Deterministic seeding** — reproducible responses for tests
- **FastAPI-native** — full OpenAPI, validation, async
- **Simulation options** — error rate, latency, rate limiting, filtering, optional response validation; OpenAPI documents 429 and simulated errors when configured
- **Extensible** — custom link types via plugins
- **Property-based testing** — Hypothesis strategies and test helpers in `semblance.property_testing`

## Next Steps

- [Getting Started](guides/getting-started.md) — full walkthrough
- [Concepts](guides/concepts.md) — input/output models, links, seeding, stateful store
- [Input and Output Binding](guides/input-output-binding.md) — FromInput, DateRangeFrom, and more
- [Simulation Options](guides/simulation-options.md) — error rate, latency, rate limiting, response validation
- [Testing](guides/testing.md) — test_client, property-based testing with Hypothesis
- [Examples](examples/README.md) — runnable examples
- [API Reference](api/index.md) — module reference
- [Roadmap](roadmap.md) — phases and status
