# Semblance

**Schema-driven REST API simulation** using FastAPI, Pydantic, and Polyfactory.

Define API behaviour with schemas and dependency metadata—no endpoint logic required.

## Install

```bash
pip install semblance
```

Requires Python 3.10+.

## Quick start

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

Run with `uvicorn app:app` and call `GET /users?name=alice&start_date=2024-01-01&end_date=2024-12-31`. Responses are generated from your output model, with `name` bound from the query and `created_at` random in the date range.

## Testing

```python
from semblance import SemblanceAPI, test_client

# Build app (register endpoints as above)
app = api.as_fastapi()
client = test_client(app)

r = client.get("/users?name=testuser")
assert r.status_code == 200
data = r.json()
assert all(u["name"] == "testuser" for u in data)
```

## Phase 1, 2 & 3 status

- SemblanceAPI core, GET and POST endpoints
- Query parameter and body inputs, path parameters (`/users/{id}`)
- Single, list, and `PaginatedResponse[Model]` outputs
- `FromInput`, `DateRangeFrom`, `WhenInput`, `ComputedFrom`, `PageParams`, `PaginatedResponse`
- `list_count="limit"` to bind list length to input
- Deterministic seeding: `SemblanceAPI(seed=42)` or `seed_from="seed"`
- Error simulation: `error_rate=0.1`, `error_codes=[404, 500]`
- Latency simulation: `latency_ms=100`, `jitter_ms=20`
- Conditional dependencies: `WhenInput("field", value, FromInput("x"))`
- Cross-field: `ComputedFrom(("a", "b"), lambda a, b: f"{a} {b}")`
- Nested model linking (links resolved inside nested BaseModel fields)
- Collection filtering: `filter_by="status"`
- Stateful mode: `SemblanceAPI(stateful=True)` - POST stores, GET returns stored

See [docs/semblance_planning_and_roadmap.md](docs/semblance_planning_and_roadmap.md) for full roadmap.
