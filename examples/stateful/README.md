# Stateful collections example

POST creates and stores users; GET returns the stored collection. For by-ID lookups, updates, and deletion, see the stateful CRUD example.

[Python source](https://github.com/eddiethedean/semblance/blob/main/examples/stateful/app.py)

## Code

```python
"""
Stateful example - POST stores items, GET returns stored list.

Run: semblance run examples.stateful.app:api --port 8000
"""

from typing import Annotated

from pydantic import BaseModel
from semblance import FromInput, SemblanceAPI


class CreateUser(BaseModel):
    """POST body for creating a user."""

    name: str = "alice"


class UserWithId(BaseModel):
    id: str = ""
    name: Annotated[str, FromInput("name")]


api = SemblanceAPI(stateful=True)


@api.post("/users", input=CreateUser, output=UserWithId, summary="Create user")
def create_user():
    """Creates user and stores in state. Returns stored instance with id."""
    pass


@api.get("/users", input=CreateUser, output=list[UserWithId], summary="List users")
def list_users():
    """Returns all stored users (stateful)."""
    pass


app = api.as_fastapi()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
```

## Run

From the repository root, with Semblance installed:

```bash
semblance run examples.stateful.app:api --port 8000
```

## Requests and responses

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

Exact generated values can change with dependency versions.

## Further reading

See the [guide](../../docs/guides/stateful-mode.md) for the behavior and available options.
