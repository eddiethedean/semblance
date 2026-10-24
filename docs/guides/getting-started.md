# Getting started

Build a simulator that returns users whose names and creation dates come from the request. This walkthrough uses a fixed seed and two results so you can compare your response with the output below.

## Install

Use **Python 3.10+**:

```bash
pip install semblance
```

The package includes FastAPI, Pydantic, Polyfactory, Uvicorn, and the `semblance` command.

## Describe the request and response

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

`UserQuery` defines the accepted query parameters. `User` defines the response fields. `FromInput("name")` copies the requested name, and `DateRangeFrom(...)` generates timestamps within the requested date range.

The function body is a registration placeholder. Semblance ignores it when generating responses.

## Validate and run

From the directory containing `app.py`, validate the route bindings:

```bash
semblance validate app:api
```

Successful validation prints `OK` and exits with status 0. Start the API:

```bash
semblance run app:api --port 8000
```

For automatic reload while editing, serve the exported FastAPI instance:

```bash
semblance run app:app --port 8000 --reload
```

You can also use `uvicorn app:app --reload`. Use one server command at a time.

## Send a request

In another terminal:

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

The request uses the model's default dates. Override any input in the query:

```bash
curl "http://127.0.0.1:8000/users?name=bob&start_date=2024-01-01&end_date=2024-12-31"
```

**Output — `200 OK`:**

```json
[
  {"name": "bob", "created_at": "2024-08-22T00:43:29.352128"},
  {"name": "bob", "created_at": "2024-01-10T03:41:40.080943"}
]
```

With the same seed, date range, and dependency versions, the generated timestamps repeat. Pydantic validates incoming values; for example, `start_date=not-a-date` returns `422 Unprocessable Entity`.

## Explore the contract

- Open [localhost:8000/docs](http://127.0.0.1:8000/docs) for the interactive API explorer.
- Fetch `/openapi.json` for the generated schema.
- Install the optional HTTP client used to sample endpoint responses:

  ```bash
  pip install httpx
  ```

- Export it with `semblance export openapi app:api -o openapi.json`.

## Next steps

| Task | Guide |
|---|---|
| Add realistic names and emails | [Realistic data with Capper](realistic-data.md) |
| Write a pytest test for this API | [Testing](testing.md) |
| Return a temporary failure, then recover | [Simulation options](simulation-options.md#scenario-steps) |
| Add POST, lookups, updates, and deletes | [Stateful mode](stateful-mode.md) |
| Understand generation and seeding | [Concepts](concepts.md) |
