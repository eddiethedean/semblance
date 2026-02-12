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

## Phase 1 (MVP) status

- SemblanceAPI core
- GET endpoints with query parameter inputs
- Single and list outputs
- `FromInput` and `DateRangeFrom` links
- Polyfactory integration and FastAPI app export
- Basic pytest client (`semblance.test_client(app)`)

See [docs/semblance_planning_and_roadmap.md](docs/semblance_planning_and_roadmap.md) for full roadmap.
