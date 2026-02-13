# Stateful Example

POST creates and stores items; GET list returns stored instances.

## Code

```python
"""
Stateful example - POST stores items, GET returns stored list.
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
```

## Run

```bash
semblance run examples.stateful.app:api --port 8000
```

## Try

```bash
# Create users
curl -X POST "http://127.0.0.1:8000/users" -H "Content-Type: application/json" -d '{"name":"alice"}'
curl -X POST "http://127.0.0.1:8000/users" -H "Content-Type: application/json" -d '{"name":"bob"}'

# List stored users
curl "http://127.0.0.1:8000/users?name=x"
```

Example responses (IDs vary per run):

```json
// POST alice
{"id": "hCnVvpUeXBVQBtxIbCrv", "name": "alice"}

// POST bob
{"id": "HCmJJfYwGIBzngQDycHu", "name": "bob"}

// GET /users
[
  {"id": "hCnVvpUeXBVQBtxIbCrv", "name": "alice"},
  {"id": "HCmJJfYwGIBzngQDycHu", "name": "bob"}
]
```

## Concepts

- **stateful=True** – SemblanceAPI stores POST responses
- **GET list** – returns stored instances, not newly generated
- **id** – auto-generated for models with id field
- State is process-local (in-memory)
